# Offline bootstrap notes

The bootstrap wheelhouse is intentionally allowed to contain small platform-support packages that are not used on every host. In particular, `colorama==0.4.6` is pinned explicitly so a Linux-connected builder cannot omit pytest's Windows-only transitive dependency while producing the Windows wheelhouse.
