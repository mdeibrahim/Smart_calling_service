# Secrets Rotation Required - CRITICAL

## ⚠️ IMMEDIATE ACTION REQUIRED

The following secrets were **permanently exposed** in git history (commit `f98d1ed`):

| Secret Type | Exposed Value | Action Required |
|-------------|---------------|-----------------|
| Django SECRET_KEY | `<REDACTED>` | **ROTATE IMMEDIATELY** |
| ZOHO Email Password | `<REDACTED>` | **ROTATE IMMEDIATELY** |
| ZOHO_CLIENT_ID | `<REDACTED>` | Regenerate OAuth credentials |
| ZOHO_CLIENT_SECRET | `<REDACTED>` | Regenerate OAuth credentials |

## Git History Cleanup

### Option 1: Using BFG Repo-Cleaner (Recommended)

1. Install Java (required for BFG)
2. Download BFG: https://rtyley.github.io/bfg-repo-cleaner/
3. Run these commands:

```bash
# Clone a fresh copy (DO NOT use your existing repo)
git clone --mirror git@github.com:your-org/your-repo.git temp-repo
cd temp-repo

# Run BFG to replace all secrets
bfg --replace-text <(echo "
django-insecure-24f5e@!)uckgq3vqckh&zo2\$m8v\$bx)4d8=_*de5xg26*hksmk==>SECRET_KEY_PLACEHOLDER
REDACTED_ZOHO_PASSWORD==>ZOHO_PASSWORD_PLACEHOLDER
REDACTED_ZOHO_CLIENT_ID==>ZOHO_CLIENT_ID_PLACEHOLDER
REDACTED_ZOHO_CLIENT_SECRET==>ZOHO_CLIENT_SECRET_PLACEHOLDER
")

# Push cleaned history
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

### Option 2: Using git filter-repo (Faster)

```bash
# Install git-filter-repo
pip install git-filter-repo

# Clone fresh copy
git clone --mirror git@github.com:your-org/your-repo.git temp-repo
cd temp-repo

# Run filter-repo with replacement file
git filter-repo --replace-text <(echo "
django-insecure-24f5e@!)uckgq3vqckh&zo2\$m8v\$bx)4d8=_*de5xg26*hksmk==>SECRET_KEY_PLACEHOLDER
REDACTED_ZOHO_PASSWORD==>ZOHO_PASSWORD_PLACEHOLDER
REDACTED_ZOHO_CLIENT_ID==>ZOHO_CLIENT_ID_PLACEHOLDER
REDACTED_ZOHO_CLIENT_SECRET==>ZOHO_CLIENT_SECRET_PLACEHOLDER
")

# Push cleaned history
git push --force
```

## After Cleanup

1. **Update all team members** - They must re-clone the repository
2. **Set environment variables** - Use `.env.example` as reference
3. **Verify no secrets remain**:
   ```bash
   git log --all --p -S "REDACTED_ZOHO_PASSWORD" --source --remotes --tags --graph
   ```

## Created Files

- `.env.example` - Template for environment variables (should be committed)
- `.gitignore` - Already includes `*.sqlite3` and `db.sqlite3`

## Status

- [ ] Rotate Django SECRET_KEY
- [ ] Reset ZOHO email password
- [ ] Regenerate ZOHO OAuth credentials (client ID and secret)
- [ ] Run BFG or git-filter-repo to clean history
- [ ] Verify cleanup
- [ ] Notify team to re-clone repository

---
*Generated: 2026-03-12*
