from errno import EEXIST
from os import makedirs, path
from string import Template

def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.

    Parameters
    ----------
    filename : string
        full filename and path

    Returns
    -------
    names : list
        a list of names in order.
    emails : list
        a list of email addresses in the same order.

    """
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def read_template(filename):
    """
    Returns a Template object comprising the contents of the 
    file specified by filename.    

    Parameters
    ----------
    filename : string
        full filename path.

    Returns
    -------
        a Template object

    """

    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def mkdir_p(mypath):
    """
    Creates a directory. equivalent to using mkdir -p on the command line

    Parameters
    ----------
    mypath : string
        folder path.

    Returns
    -------
    None.

    """

    try:
        makedirs(mypath)
    except OSError as exc:  # Python >2.5
        if exc.errno == EEXIST and path.isdir(mypath):
            pass
        else:
            raise