overview
--------

(under development -- not yet in production)

This code aims to improve the process of requesting _items_ at the [Annex](http://library.brown.edu/about/annex/), the [Library's](http://library.brown.edu/) offsite storage facility. ([Other code](https://github.com/Brown-University-Library/easyscan) handles requesting _scans_ from the Annex.)

The current system involves multiple steps and is confusing.

Note: there is nothing annex-specific about the code, so it could be used to automate requesting of other items in the future.


basic flow
----------

user's experience...
- user clicks a 'request item' link that lands at this app
- after authenticating, user sees a confirmation message and receives a confirmation email

detail flow...
- user initially lands at login page
    - data from url stored to session
    - item-id determined from submitted bib and item-barcode via availability-api call
- user clicks 'login' button, accessing shib-protected view
    - after passing shib, view captures shib-supplied user name, barcode, and email
    - user redirected to hidden 'processing' page
- processing page:
    - uses the [josiah-patron-accounts](https://github.com/Brown-University-Library/josiah-patron-accounts) code to place a millennium request on behalf of the user
    - sends user confirmation email
    - redirects user to final summary page

urls & params
-------------

- The root `scheme://host/easyrequest` will redirect to the info page at `scheme://host/easyrequest/info/`
- A typical url may look like: `scheme://host/easyrequest/login?bibnum=b12345678&barcode=31236090031116`
- required params
    - `bibnum` -- used to get list of item records
    - `barcode` -- (this is the _item_ barcode) used to identify which item in list user wants

geek tech
---------
- the `requirements.txt` [shellvars-py](https://github.com/aneilbaboo/shellvars-py) import isn't strictly necessary, but it nicely allows env/bin/activate and env/bin/activate_this.py to access the same local_settings.sh file.

contacts
--------

- birkin_diana at brown dot edu

---
