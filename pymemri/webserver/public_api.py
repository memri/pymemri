from inspect import getfullargspec

ENDPOINT_METADATA = "__endpoint_metadata__"


def register_endpoint(endpoint_name: str, method: str):
    """Registers `fn` under endpoint `endpoint_name` into the webserver as public API.
    The `method` parameter specifies HTTP operation: GET, POST, DELETE, etc.
    The `fn` needs to pass the validation, for example cannot contain *args, **kwargs,
    all arguments needs to have type annotation."""

    def _add_endpoint_metadata_attr(fn):
        args = getfullargspec(fn)

        # *args makes fastapi crash upon calling the handler
        if args.varargs:
            raise RuntimeError(f"passed function cannot have *args")

        # Allowing **kwargs:
        # - leaks python detail to the API
        # - is treated as string in query parameter: "{"key": value, ...}", instead of {"key": value}
        if args.varkw:
            raise RuntimeError(f"passed function cannot have **kwargs")

        # Requiring typing enforces api clarity
        missing_annotations = []
        for arg in args.args:
            if arg != "self" and arg not in args.annotations:
                missing_annotations.append(arg)

        if missing_annotations:
            raise RuntimeError(f"arguments: {missing_annotations} does not have type annotation")

        metadata = (endpoint_name, method)

        # Prevent nested decoration
        if hasattr(fn, ENDPOINT_METADATA):
            raise RuntimeError(
                f"Trying to register function {fn.__name__} to {metadata} but is already used in: {fn.__endpoint_metadata__}"
            )

        fn.__endpoint_metadata__ = metadata
        return fn

    return _add_endpoint_metadata_attr
