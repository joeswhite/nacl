
class StateRegistry(object):
    """
    The StateRegistry holds all of the states that have been created.
    """

    def __init__(self):
        self.empty()

    def empty(self):
        self.states = {}

    def add(self, name, state):
        if name in self.states:
            raise Exception("TODO: Make this better")

        self.states[name] = state

default_registry = StateRegistry()


class StateFactory(object):
    """
    The StateFactory is used to generate new States through a natural syntax

    It is used by initializing it with the name of the salt module::

        File = StateFactory("file")

    Any attribute accessed on the instance returned by StateFactory is a lambda
    that is a short cut for generating State objects::

        File.managed('/path/', owner='root', group='root')

    The kwargs are passed through to the State object
    """
    def __init__(self, module, registry=None):
        self.module = module
        if registry is not None:
            self.registry = registry
        else:
            self.registry = default_registry

    def __getattr__(self, func):
        return lambda name, **k: State(
            name,
            ".".join([self.module, func]),
            registry=self.registry,
            **k
        )

    def __call__(self, name):
        """
        When an object is called it is being used as a requisite
        """
        # return the correct data structure for the requisite
        return {self.module: name}


class State(object):
    """
    This represents a single item in the state tree

    The name is the name of the state, the func is the full name of the salt
    state (ie. file.managed). All the keyword args you pass in become the
    properties of your state.

    The registry is where the state should be stored. It is optional and will
    use the default registry if not specified.
    """

    def __init__(self, name, func, registry=None, **kwargs):
        self.name = name
        self.func = func

        # store our raw kwargs, but also store a copy in the format the salt
        # state needs to be built in. we sort the kwargs by key so that we
        # have consistent ordering for tests
        self.kwargs = kwargs
        self.attrs = [
            {k: kwargs[k]}
            for k in sorted(kwargs.iterkeys())
        ]

        # handle some "special" cases

        # our requisites should all be lists, but when you only have a single
        # one it's more convenient to provide it without wrapping it in a list.
        # if that's the case wrap it in a list
        for attr in ('require', 'watch', 'require_in', 'watch_in'):
            if attr in self.attrs and not isinstance(self.attrs[attr], list):
                self.attrs[attr] = [self.attrs[attr]]

        if registry is None:
            registry = default_registry
        registry.add(name, self)

    def __str__(self):
        return "%s = %s:%s" % (self.name, self.func, self.attrs)

    def serialize(self):
        return (self.name, {self.func: self.attrs})
