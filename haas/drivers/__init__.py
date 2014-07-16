"""Network switch drivers for the HaaS.

This package provides HaaS drivers for various network switches. The
functions in the top-level module should not be used; they only exist
as a place to document the interface shared by all of the drivers.

Port IDs and network IDs should both be strings.  The content of them will be
driver-specific.

"""


def apply_networking(net_map):
    """Takes in a dictionary, mapping port IDs to network IDs.

    For each key-value pair (port, network) in the dictionary, set that port
    to access that network.  If network is None, set it to access nothing.
    """

def get_new_network_id(db):
    """Gets a new network ID, valid for this driver.  Returns 'None' if there
    are no more possible IDs available.  Pass in the database connection, to
    make the allocation part of the current transaction.
    """

def free_network_id(db, net_id):
    """Marks a network ID as unused, so that it can be re-used for a new
    network.  Can be a no-op on some drivers.  Pass in the database
    connection, to make the freeing part of the current transaction.
    """

def init_db():
    """Initializes any database tables and/or objects that the driver needs to
    have to function correctly.
    """
