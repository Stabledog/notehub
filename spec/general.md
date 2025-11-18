# General guidance and policies


1. Code Comments:
    - Comments in code should avoid restating the obvious:
    ```py
    #  BAD!
    #  Open the file
    with open("myfile","r") as file:
    ```

    - It is OK summarize if there's complexity.  Keep it short.
    ```py
    #  OK!
    # We need a union of the type traits which have been filtered by the filter chain,
    # because only unions are accepted by the downstream service zfiltsvc, which performs
    # poorly if it gets traits that don't resolve in the current context:
    forward_traits_union = [ tx for tx in filter_chain( aggr_traits( t for t in entity.traits(), chain))  ]
    ```
    (The programmer can read and understand *what* is happening without the comment, but may be 
    mystified about the needs of the downstream service which is not obivous in the bare code)

    - TODOs are useful when known shortcomings or provisional hacks are present:
    ```py
    #  OK!
    # TODO: we can't read from a file in all use cases, so 'filename' is going to need to be abstracted:
    filename='/tmp/instream.json'
    with open(filename,...

1. Authentication and context resolution

Working with the `gh` authentication is tricky.  `gh_wrapper.py` does what works, and that may not agree with public sources about best-practices or the recommendations of the `gh` owners.

Do not vary from using `_prepare_gh_cmd`, `_handle_gh_error`, etc.  We want all commands to use consistent interaction patterns with `gh` to avoid chaos.

