import datetime

def make_base_dt(value):
    """
    Create a copy of `value` using datetime baseclass. This allows us to do datetime arithmetic on Python 3.8+
    Args:
        value (pyxb.binding.datatypes.datetime): PyXB datetime object

    Returns:
        datetime.datetime: Matching datetime base instance
    """
    return datetime.datetime(
        value.year, 
        value.month, 
        value.day, 
        value.hour, 
        value.minute, 
        value.second, 
        value.microsecond, 
        tzinfo=value.tzinfo
    )
