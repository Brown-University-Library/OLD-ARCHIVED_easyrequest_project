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
    - data from url is stored to session
    - item-id is determined from submitted bib and item-barcode via a call to an [availability-api](https://github.com/Brown-University-Library/availability-service) (a different availability-api may ultimately be called)
- user logs in, either via shib or via the old-school [barcode+name method](https://josiah.brown.edu/patroninfo)
    - if logging in via barcode+name method, a lookup is also done on a [patron-api](https://github.com/birkin/patron_api_web) web-service to get name and email info
    - user is redirected to hidden 'processing' page
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

contacts
--------

- birkin_diana at brown dot edu

---
