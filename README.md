# seagent-hackathon


# save conda env
# Conda Environment Setup

This guide explains how to save, recreate, and manage a Conda environment efficiently.

## Save Conda Environment

To export your current Conda environment into a minimal `environment.yml` file (without versions), run:

```bash
conda env export --from-history > environment.yml       
```