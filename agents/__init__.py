"""ForexAI agent modules.

The package marker is intentional: the dependency set includes a third-party
package named ``agents`` (via the Agents SDK). Without a local package marker,
Python can resolve that dependency instead of this repository's ``agents``
namespace when executing ``python -m agents.<module>``.
"""
