def _register(kind):
    def decorator(fn=None, *, transitions_to=None):
        if fn is not None:
            # Bare decorator: @step
            fn.__fabrikk__ = {
                "kind": kind,
                "name": fn.__name__,
                "transitions_to": None,
            }
            return fn

        # Parameterized decorator: @step(transitions_to=[...])
        def wrapper(fn):
            fn.__fabrikk__ = {
                "kind": kind,
                "name": fn.__name__,
                "transitions_to": transitions_to,
            }
            return fn
        return wrapper

    return decorator


start = _register("start")
step = _register("step")
finish = _register("finish")
