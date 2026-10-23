# Grant laptop read-only diagnostic v1

This script is an inventory, not a production acceptance gate or trading authorization. Run it on the selected Windows laptop from a repository checkout:

    .\tools\diagnose_capital_firewall_laptop_v1.ps1

It inventories six public trust-anchor environment variables in Process/User/Machine scopes, checks canonical base64 raw-32-byte key shape and duplicate public-key material per scope, compares the Grant public-key file against environment anchors, reports ACL rules for the private-key file/public-key file/key directory, and checks candidate Grant SQLite registries through a read-only connection.

The script never prints key values or passphrases, reads private-key contents, changes ACLs/environment/files/services/registry, initializes or resets a database, issues a Grant, creates an Admission request, or submits an order. Production authorization flags are hard-coded false. Public-key fingerprints are short hashes of public keys.

ACL entries are not a full Windows effective-access evaluation. The script cannot inspect a remote Provider host. Its laptop Promotion-anchor findings must be compared to the remote Provider diagnostics and Promotion key owner; the already-recorded remote Promotion mismatch remains unresolved until an owner-approved repair is verified. Presence of an anchor does not prove an operational Signal, Risk/Reservation, or Operator service.
