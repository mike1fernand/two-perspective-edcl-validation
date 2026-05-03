# PantheonPlus data provenance note

## Current status

This provenance note is **not yet complete**.

The repository currently uses the Cobaya likelihood key:

```text
sn.pantheonplus
```

together with a separate local-H0 likelihood in the late-only Tier-A1 configurations. That combination creates a potential double-counting question: the repository must document that the installed PantheonPlus configuration used for the quoted runs does **not** already embed SH0ES/local-H0 calibration information.

Until the exact installed dataset files and component metadata are documented from the validated Cobaya environment, paper wording should not claim full referee-grade exclusion of SN/local-H0 double counting.

## Why this matters

The intended Tier-A1 separation is:

```text
PantheonPlus: supernova likelihood
H0_edcl: separate observed-frame local-H0 likelihood
```

For EDCL+local-H0 runs, the local anchor is applied through:

```text
H0_obs = H0 * (1 + alpha_R * 0.7542)
```

using the custom `H0_edcl` likelihood. If the selected PantheonPlus component already contains an embedded SH0ES/local-H0 calibration, then the local-H0 information could be counted twice.

## Current safe claim

Use this wording until the provenance fields below are filled:

```text
The late-only Tier-A1 configuration uses Cobaya `sn.pantheonplus` together with a separate observed-frame local-H0 likelihood. The repository includes guards against explicit local-H0 likelihood double counting in the rendered YAMLs, but the exact PantheonPlus package files and no-embedded-SH0ES evidence still need to be documented from the validated Cobaya installation logs before making a full referee-grade double-counting-exclusion claim.
```

Do **not** use wording such as:

```text
PantheonPlus is proven unanchored in the validated Tier-A1 run.
```

until the evidence below is filled from real logs/package metadata.

## Evidence still required

Fill in these fields from the validated Cobaya installation and run workdir.

### 1. Cobaya component

```text
Component key: sn.pantheonplus
Cobaya version: <fill from environment manifest or cobaya log>
Cobaya package path: <fill from validated workdir/logs>
Component source/version/hash: <fill from package metadata or install log>
```

### 2. Exact dataset files used

List the actual installed files used by the `sn.pantheonplus` likelihood:

```text
<dataset file 1>
<dataset file 2>
<covariance file>
<metadata/config file>
```

Source for these filenames:

```text
<cobaya-install log, package directory listing, or validated workdir file>
```

### 3. Evidence for no embedded SH0ES/local-H0 calibration

Provide one or more of the following:

```text
package documentation excerpt
component configuration flag
dataset metadata statement
Cobaya likelihood source/config evidence
validated package file inspection
```

Record the evidence here:

```text
<fill with exact evidence>
```

### 4. Rendered YAML cross-check

For the no-local-H0 control, record the rendered YAML path and hash:

```text
Rendered YAML: <workdir>/yamls/edcl_cosmo_lateonly_no_sh0es.yaml
SHA256: <fill>
```

Confirm:

```text
H0_edcl absent: <yes/no>
H0.riess2020 absent: <yes/no>
sh0es marker absent from rendered YAML: <yes/no>
sn.pantheonplus present: <yes/no>
```

### 5. Guard-script output

Record the output of:

```bash
python3 cosmology/scripts/check_no_doublecount_sh0es.py <rendered-yaml-or-workdir>
```

Result:

```text
<fill with pass/warn/fail output>
```

## Resolution criterion

This note can be marked complete only when:

```text
1. The validated Cobaya version is recorded.
2. The actual PantheonPlus dataset/config files are listed.
3. Evidence for no embedded SH0ES/local-H0 calibration is recorded.
4. The rendered no-H0 YAML is shown to contain no explicit local-H0 likelihood.
5. The guard-script output is recorded.
```

## Status marker

```text
status: unresolved_provenance_note
```
