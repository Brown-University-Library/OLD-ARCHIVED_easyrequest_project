overview
--------

This code aims to improve the process of requesting items at the [Annex](http://library.brown.edu/about/annex/), the Library's offsite storage facility.

The current system involves multiple steps and is confusing.

Note: there is nothing annex-specific about the code, so it could be used to automate requesting of other items in the future.


basic flow
----------

user's experience...
- user clicks a 'request item' link that lands at this app
- after authenticating, user sees a confirmation message

behind the scenes...
- after user authenticates, app uses the [josiah-patron-accounts](https://github.com/Brown-University-Library/josiah-patron-accounts) code to place a millennium request on behalf of the user
- how:
    - the bibnum param is used to get a list of items
    - the barcode param is used to identify the item desired (and item-number is grabbed)
    - the item-number is used to place the request

urls & params
-------------

- The root `scheme://host/easyrequest` will redirect to the info page at `scheme://host/easyrequest/info/`
- The root request url: `scheme://host/easyrequest/item`
- A typical url may look like: `scheme://host/easyrequest/item?bibnum=b12345678&barcode=31236090031116`
- required params
    - `bibnum` -- used to get list of item records
    - `barcode` -- (this is the item barcode) used to identify which item in list user wants

contacts
--------

- birkin_diana at brown dot edu
- ted_lawless at brown dot edu

---
