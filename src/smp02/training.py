from __future__ import annotations

from pathlib import Path

import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader
from tqdm.auto import tqdm

from smp02.vae import (
    SmilesOneHotDataset,
    SmilesVAE,
    cosine_similarity,
    decoded_validity,
    save_vae_checkpoint,
    vae_loss,
)


def _maybe_parallel(model: nn.Module, device: torch.device) -> nn.Module:
    if device.type == "cuda" and torch.cuda.device_count() > 1:
        return nn.DataParallel(model)
    return model


def _loader_kwargs(num_workers: int) -> dict:
    if num_workers <= 0:
        return {}
    return {"persistent_workers": True, "prefetch_factor": 4}


def train_vae_model(
    smiles: list[str],
    charset: list[str],
    max_length: int,
    latent_size: int,
    out_path: str | Path,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    device: torch.device,
    num_workers: int = 0,
    reconstruction_weight: float = 1.0,
    kl_weight: float = 1.0,
    validity_weight: float = 0.1,
) -> list[dict[str, float]]:
    dataset = SmilesOneHotDataset(smiles, charset, max_length)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=device.type == "cuda",
        **_loader_kwargs(num_workers),
    )
    model = SmilesVAE(latent_size=latent_size, max_length=max_length, charset_size=len(charset)).to(device)
    model = _maybe_parallel(model, device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    metrics: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        totals = {"loss": 0.0, "reconstruction": 0.0, "kl": 0.0, "validity": 0.0, "cosine": 0.0}
        batches = 0
        for x in tqdm(loader, desc=f"pretrain latent={latent_size} epoch={epoch}/{epochs}", leave=False):
            x = x.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits, mu, logvar = model(x)
            loss, parts = vae_loss(logits, x, mu, logvar, reconstruction_weight, kl_weight)
            validity = decoded_validity(logits, charset)
            validity_penalty = torch.tensor((1.0 - validity) * validity_weight, device=device)
            total_loss = loss + validity_penalty
            total_loss.backward()
            optimizer.step()
            totals["loss"] += float(total_loss.detach())
            totals["reconstruction"] += parts["reconstruction"]
            totals["kl"] += parts["kl"]
            totals["validity"] += validity
            totals["cosine"] += cosine_similarity(logits, x)
            batches += 1
        row = {"epoch": float(epoch), **{k: v / max(batches, 1) for k, v in totals.items()}}
        metrics.append(row)
        save_vae_checkpoint(out_path, model, charset, max_length, latent_size, metrics)
    pd.DataFrame(metrics).to_csv(Path(out_path).with_suffix(".metrics.csv"), index=False)
    return metrics


def fine_tune_vae_decoder(
    pretrained_path: str | Path,
    smiles: list[str],
    out_path: str | Path,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    device: torch.device,
    num_workers: int = 0,
    reconstruction_weight: float = 1.0,
    kl_weight: float = 1.0,
    validity_weight: float = 0.1,
) -> list[dict[str, float]]:
    from smp02.vae import load_vae_checkpoint

    base_model, checkpoint = load_vae_checkpoint(pretrained_path, map_location=device)
    charset = checkpoint["charset"]
    max_length = int(checkpoint["max_length"])
    latent_size = int(checkpoint["latent_size"])
    for param in base_model.encoder_conv.parameters():
        param.requires_grad = False
    for param in base_model.fc_mu.parameters():
        param.requires_grad = False
    for param in base_model.fc_logvar.parameters():
        param.requires_grad = False
    base_model.to(device)
    model = _maybe_parallel(base_model, device)
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.Adam(trainable, lr=learning_rate)
    dataset = SmilesOneHotDataset(smiles, charset, max_length)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=device.type == "cuda",
        **_loader_kwargs(num_workers),
    )
    metrics: list[dict[str, float]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        totals = {"loss": 0.0, "reconstruction": 0.0, "kl": 0.0, "validity": 0.0, "cosine": 0.0}
        batches = 0
        for x in tqdm(loader, desc=f"finetune latent={latent_size} epoch={epoch}/{epochs}", leave=False):
            x = x.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits, mu, logvar = model(x)
            loss, parts = vae_loss(logits, x, mu, logvar, reconstruction_weight, kl_weight)
            validity = decoded_validity(logits, charset)
            total_loss = loss + torch.tensor((1.0 - validity) * validity_weight, device=device)
            total_loss.backward()
            optimizer.step()
            totals["loss"] += float(total_loss.detach())
            totals["reconstruction"] += parts["reconstruction"]
            totals["kl"] += parts["kl"]
            totals["validity"] += validity
            totals["cosine"] += cosine_similarity(logits, x)
            batches += 1
        row = {"epoch": float(epoch), **{k: v / max(batches, 1) for k, v in totals.items()}}
        metrics.append(row)
        save_vae_checkpoint(out_path, model, charset, max_length, latent_size, metrics)
    pd.DataFrame(metrics).to_csv(Path(out_path).with_suffix(".metrics.csv"), index=False)
    return metrics
