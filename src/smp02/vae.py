from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import Dataset

from smp02.data import canonicalize_smiles

PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
BASE_CHARS = list("#%()+-./0123456789:=@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]\\abcdefghijklmnopqrstuvwxyz")
EXTRA_TOKENS = list("!$&*?,;<>^_`{|}~")


def build_charset(smiles: Iterable[str], min_size: int = 55) -> list[str]:
    chars = sorted({ch for smi in smiles for ch in smi})
    charset = [PAD_TOKEN, UNK_TOKEN]
    for ch in BASE_CHARS + chars + EXTRA_TOKENS:
        if ch not in charset:
            charset.append(ch)
        if len(charset) >= min_size and set(chars).issubset(set(charset)):
            break
    for ch in chars:
        if ch not in charset:
            charset.append(ch)
    return charset


def smiles_to_matrix(smiles: str, charset: list[str], max_length: int) -> np.ndarray:
    index = {token: i for i, token in enumerate(charset)}
    mat = np.zeros((max_length, len(charset)), dtype=np.float32)
    pad_idx = index[PAD_TOKEN]
    unk_idx = index[UNK_TOKEN]
    mat[:, pad_idx] = 1.0
    for row, ch in enumerate(smiles[:max_length]):
        mat[row, pad_idx] = 0.0
        mat[row, index.get(ch, unk_idx)] = 1.0
    return mat


def matrix_to_smiles(matrix: torch.Tensor | np.ndarray, charset: list[str]) -> str:
    if isinstance(matrix, torch.Tensor):
        indices = matrix.detach().cpu().argmax(dim=-1).tolist()
    else:
        indices = np.asarray(matrix).argmax(axis=-1).tolist()
    tokens = []
    for idx in indices:
        token = charset[int(idx)]
        if token in {PAD_TOKEN, UNK_TOKEN}:
            continue
        tokens.append(token)
    return "".join(tokens)


class SmilesOneHotDataset(Dataset[torch.Tensor]):
    def __init__(self, smiles: Iterable[str], charset: list[str], max_length: int) -> None:
        self.smiles = list(smiles)
        self.charset = charset
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.smiles)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return torch.from_numpy(smiles_to_matrix(self.smiles[idx], self.charset, self.max_length))


class SmilesVAE(nn.Module):
    def __init__(self, latent_size: int, max_length: int = 204, charset_size: int = 55) -> None:
        super().__init__()
        self.latent_size = latent_size
        self.max_length = max_length
        self.charset_size = charset_size
        self.encoder_conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 8, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((14, 13)),
        )
        self.conv_flat_size = 8 * 14 * 13
        self.fc_mu = nn.Linear(self.conv_flat_size, latent_size)
        self.fc_logvar = nn.Linear(self.conv_flat_size, latent_size)
        self.decoder_fc = nn.Linear(latent_size, self.conv_flat_size)
        self.decoder_conv = nn.Sequential(
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Upsample(size=(max_length, charset_size), mode="bilinear", align_corners=False),
            nn.Conv2d(16, 2, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(2, 1, kernel_size=3, padding=1),
        )

    def encode(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = x.unsqueeze(1)
        h = self.encoder_conv(x).flatten(1)
        return self.fc_mu(h), self.fc_logvar(h)

    @staticmethod
    def reparameterize(mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        if not torch.is_grad_enabled():
            return mu
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        h = self.decoder_fc(z).view(-1, 8, 14, 13)
        return self.decoder_conv(h).squeeze(1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar


def vae_loss(
    logits: torch.Tensor,
    target: torch.Tensor,
    mu: torch.Tensor,
    logvar: torch.Tensor,
    reconstruction_weight: float = 1.0,
    kl_weight: float = 1.0,
) -> tuple[torch.Tensor, dict[str, float]]:
    reconstruction = F.binary_cross_entropy_with_logits(logits, target, reduction="mean")
    kl = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    loss = reconstruction_weight * reconstruction + kl_weight * kl
    return loss, {"reconstruction": float(reconstruction.detach()), "kl": float(kl.detach())}


def decoded_validity(logits: torch.Tensor, charset: list[str], sample_size: int = 16) -> float:
    probs = torch.sigmoid(logits[:sample_size])
    decoded = [matrix_to_smiles(row, charset) for row in probs]
    if not decoded:
        return 0.0
    valid = sum(1 for smi in decoded if canonicalize_smiles(smi) is not None)
    return valid / len(decoded)


def cosine_similarity(logits: torch.Tensor, target: torch.Tensor) -> float:
    pred = torch.sigmoid(logits).detach().flatten(1)
    truth = target.detach().flatten(1)
    sim = F.cosine_similarity(pred, truth, dim=1)
    return float(sim.mean().detach())


def save_vae_checkpoint(
    path: str | Path,
    model: nn.Module,
    charset: list[str],
    max_length: int,
    latent_size: int,
    metrics: list[dict[str, float]] | None = None,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    module = model.module if isinstance(model, nn.DataParallel) else model
    torch.save(
        {
            "state_dict": module.state_dict(),
            "charset": charset,
            "max_length": max_length,
            "latent_size": latent_size,
            "metrics": metrics or [],
        },
        target,
    )


def load_vae_checkpoint(path: str | Path, map_location: str | torch.device = "cpu") -> tuple[SmilesVAE, dict]:
    checkpoint = torch.load(path, map_location=map_location, weights_only=False)
    model = SmilesVAE(
        latent_size=int(checkpoint["latent_size"]),
        max_length=int(checkpoint["max_length"]),
        charset_size=len(checkpoint["charset"]),
    )
    model.load_state_dict(checkpoint["state_dict"])
    return model, checkpoint


@torch.no_grad()
def encode_smiles(
    model: SmilesVAE,
    smiles: list[str],
    charset: list[str],
    max_length: int,
    device: torch.device,
    batch_size: int = 512,
) -> np.ndarray:
    model.eval()
    vectors = []
    for start in range(0, len(smiles), batch_size):
        batch_smiles = smiles[start : start + batch_size]
        batch = np.stack([smiles_to_matrix(s, charset, max_length) for s in batch_smiles])
        x = torch.from_numpy(batch).to(device)
        mu, _ = model.encode(x)
        vectors.append(mu.detach().cpu().numpy())
    if not vectors:
        return np.empty((0, model.latent_size), dtype=np.float32)
    return np.concatenate(vectors, axis=0)

