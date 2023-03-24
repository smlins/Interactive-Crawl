def script_hook(fun):
    def wrapped(*args, **kwargs):
        ret = fun(*args, **kwargs)
        return ret
    return wrapped
