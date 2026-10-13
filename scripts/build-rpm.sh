#!/usr/bin/env bash
# Run on a Fedora 44 build host with rpm-build and python3 installed.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOP="${RPMBUILD_TOPDIR:-$HOME/rpmbuild}"
mkdir -p "$TOP"/{SOURCES,SPECS,RPMS,SRPMS,BUILD,BUILDROOT}
"$ROOT/scripts/make-source-tarball.sh" "$TOP/SOURCES"
cp "$ROOT/packaging/meekro-welcome.spec" "$TOP/SPECS/"
rpmbuild --define "_topdir $TOP" -ba "$TOP/SPECS/meekro-welcome.spec"
echo "RPM files: $TOP/RPMS/noarch"
