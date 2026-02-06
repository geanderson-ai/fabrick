def _register(kind):
    def decorator(fn):
        fn.__fabrikk__ = {
            "kind": kind,
            "name": fn.__name__
        }
        return fn
    return decorator


start = _register("start")
step = _register("step")
finish = _register("finish")
