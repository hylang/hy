"""
Document Hy stuff leveraging the power of Python's built-in
pydoc.

This version overrides function and class signatures
to make them look like they are used from Hy.
"""
from __future__ import print_function

import os
import sys
import pydoc
import inspect
import argparse
import hy


def fixup_argspec(argspec):
    if argspec == '()':
        return ')'

    result = ' '
    optional = False
    # drop the opening '(' and get rid of commas
    for arg in argspec[1:].split(','):
        arg = arg.strip()
        if arg.find('=') > 0 and not optional:
            result += '&optional '
            optional = True
        elif arg.find('*args') == 0:
            result += '&rest '
            arg = arg.replace('*', '')
        elif arg.find('**kwargs') == 0:
            result += '&kwargs '
            arg = arg.replace('*', '')
        result += '%s ' % arg
    return result


class HyHTMLDoc(pydoc.HTMLDoc):
    def docclass(self, object, name=None, mod=None, funcs={}, classes={},
                 *ignored):
        """Produce HTML documentation for a class object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        contents = []
        push = contents.append

        # Cute little class to pump out a horizontal rule between sections.
        class HorizontalRule:
            def __init__(self):
                self.needone = 0

            def maybe(self):
                if self.needone:
                    push('<hr>\n')
                self.needone = 1
        hr = HorizontalRule()

        # List the mro, if non-trivial.
        mro = pydoc.deque(inspect.getmro(object))
        if len(mro) > 2:
            hr.maybe()
            push('<dl><dt>Method resolution order:</dt>\n')
            for base in mro:
                push('<dd>%s</dd>\n' % self.classlink(base,
                                                      object.__module__))
            push('</dl>\n')

        def spill(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    try:
                        value = getattr(object, name)
                    except Exception:
                        # Some descriptors may meet a failure in their __get__.
                        # (bug #1785)
                        push(self._docdescriptor(name, value, mod))
                    else:
                        push(self.document(value, name, mod,
                                           funcs, classes, mdict, object))
                    push('\n')
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    push(self._docdescriptor(name, value, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    base = self.docother(getattr(object, name), name, mod)
                    if (hasattr(value, '__call__') or
                            inspect.isdatadescriptor(value)):
                        doc = getattr(value, "__doc__", None)
                    else:
                        doc = None
                    if doc is None:
                        push('<dl><dt>%s</dl>\n' % base)
                    else:
                        doc = self.markup(pydoc.getdoc(value), self.preformat,
                                          funcs, classes, mdict)
                        doc = '<dd><tt>%s</tt>' % doc
                        push('<dl><dt>%s%s</dl>\n' % (base, doc))
                    push('\n')
            return attrs

        attrs = filter(lambda data: pydoc.visiblename(data[0], obj=object),
                       pydoc.classify_class_attrs(object))
        mdict = {}
        for key, kind, homecls, value in attrs:
            mdict[key] = anchor = '#' + name + '-' + key
            try:
                value = getattr(object, name)
            except Exception:
                # Some descriptors may meet a failure in their __get__.
                # (bug #1785)
                pass
            try:
                # The value may not be hashable (e.g., a data attr with
                # a dict or list value).
                mdict[value] = anchor
            except TypeError:
                pass

        while attrs:
            if mro:
                thisclass = mro.popleft()
            else:
                thisclass = attrs[0][2]
            attrs, inherited = \
                pydoc._split_list(attrs, lambda t: t[2] is thisclass)

            if thisclass is pydoc.__builtin__.object:
                attrs = inherited
                continue
            elif thisclass is object:
                tag = 'defined here'
            else:
                tag = 'inherited from %s' % self.classlink(thisclass,
                                                           object.__module__)
            tag += ':<br>\n'

            # Sort attrs by name.
            try:
                attrs.sort(key=lambda t: t[0])
            except TypeError:
                attrs.sort(lambda t1, t2: cmp(t1[0], t2[0]))    # 2.3 compat

            # Pump out the attrs, segregated by kind.
            attrs = spill('Methods %s' % tag, attrs,
                          lambda t: t[1] == 'method')
            attrs = spill('Class methods %s' % tag, attrs,
                          lambda t: t[1] == 'class method')
            attrs = spill('Static methods %s' % tag, attrs,
                          lambda t: t[1] == 'static method')
            attrs = spilldescriptors('Data descriptors %s' % tag, attrs,
                                     lambda t: t[1] == 'data descriptor')
            attrs = spilldata('Data and other attributes %s' % tag, attrs,
                              lambda t: t[1] == 'data')
            assert attrs == []
            attrs = inherited

        contents = ''.join(contents)

        if name == realname:
            title = '<a name="%s">(defclass <strong>%s</strong></a>' % (
                name, realname)
        else:
            title = '<strong>%s</strong> -> <a name="%s">(defclass %s</a>' % (
                name, name, realname)
        if bases:
            parents = []
            for base in bases:
                parents.append(self.classlink(base, object.__module__))
            title = title + ' [%s]' % pydoc.join(parents, ', ')
        doc = self.markup(pydoc.getdoc(object),
                          self.preformat, funcs, classes, mdict)
        doc = doc and '<tt>%s<br>&nbsp;</tt>' % doc

        return self.section(title, '#000000', '#ffc8d8', contents, 3, doc)

    def docroutine(self, object, name=None, mod=None,
                   funcs={}, classes={}, methods={}, cl=None):
        """Produce HTML documentation for a function or method object."""
        realname = object.__name__
        name = name or realname
        anchor = (cl and cl.__name__ or '') + '-' + name
        note = ''
        skipdocs = 0
        prefix = ''
        if inspect.ismethod(object):
            imclass = object.im_class
            if cl:
                if imclass is not cl:
                    note = ' from ' + self.classlink(imclass, mod)
            else:
                if object.im_self is not None:
                    note = ' method of %s instance' % self.classlink(
                        object.im_self.__class__, mod)
                else:
                    note = ' unbound %s method' % self.classlink(imclass, mod)
            object = object.im_func
            prefix = '.'

        if name == realname:
            title = '<a name="%s"><strong>(%s%s</strong></a>' \
                    % (anchor, prefix, realname)
        else:
            if (cl and realname in cl.__dict__ and
                    cl.__dict__[realname] is object):
                reallink = '<a href="#%s">%s%s</a>' % (
                    cl.__name__ + '-' + realname, prefix, realname)
                skipdocs = 1
            else:
                reallink = "."+realname
            title = '<a name="%s"><strong>%s</strong></a> -> (%s' % (
                anchor, name, reallink)
        if inspect.isfunction(object):
            args, varargs, varkw, defaults = inspect.getargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, formatvalue=self.formatvalue)
            argspec = fixup_argspec(argspec)

            if realname == '<lambda>':
                title = '<strong>%s</strong> <em>lambda</em> ' % name
                argspec = argspec[1:-1]  # remove parentheses
        else:
            argspec = ' ...)'

        decl = title + argspec + (note and self.grey(
            '<font face="helvetica, arial">%s</font>' % note))

        if skipdocs:
            return '<dl><dt>%s</dt></dl>\n' % decl
        else:
            doc = self.markup(
                pydoc.getdoc(object), self.preformat, funcs, classes, methods)
            doc = doc and '<dd><tt>%s</tt></dd>' % doc
            return '<dl><dt>%s</dt>%s</dl>\n' % (decl, doc)


class HyTextDoc(pydoc.TextDoc):
    def docclass(self, object, name=None, mod=None, *ignored):
        """Produce text documentation for a given class object."""
        realname = object.__name__
        name = name or realname
        bases = object.__bases__

        def makename(c, m=object.__module__):
            return pydoc.classname(c, m)

        if name == realname:
            title = '(defclass ' + self.bold(realname)
        else:
            title = self.bold(name) + ' -> (defclass ' + realname
        if bases:
            parents = map(makename, bases)
            title = title + ' [%s]' % pydoc.join(parents, ', ')

        doc = pydoc.getdoc(object)
        contents = doc and [doc + '\n'] or []
        push = contents.append

        # List the mro, if non-trivial.
        mro = pydoc.deque(inspect.getmro(object))
        if len(mro) > 2:
            push("Method resolution order:")
            for base in mro:
                push('    ' + makename(base))
            push('')

        # Cute little class to pump out a horizontal rule between sections.
        class HorizontalRule:
            def __init__(self):
                self.needone = 0

            def maybe(self):
                if self.needone:
                    push('-' * 70)
                self.needone = 1
        hr = HorizontalRule()

        def spill(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    try:
                        value = getattr(object, name)
                    except Exception:
                        # Some descriptors may meet a failure in their __get__.
                        # (bug #1785)
                        push(self._docdescriptor(name, value, mod))
                    else:
                        push(self.document(value,
                                           name, mod, object))
            return attrs

        def spilldescriptors(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    push(self._docdescriptor(name, value, mod))
            return attrs

        def spilldata(msg, attrs, predicate):
            ok, attrs = pydoc._split_list(attrs, predicate)
            if ok:
                hr.maybe()
                push(msg)
                for name, kind, homecls, value in ok:
                    if (hasattr(value, '__call__') or
                            inspect.isdatadescriptor(value)):
                        doc = pydoc.getdoc(value)
                    else:
                        doc = None
                    push(self.docother(getattr(object, name),
                                       name, mod, maxlen=70, doc=doc) + '\n')
            return attrs

        attrs = filter(lambda data: pydoc.visiblename(data[0], obj=object),
                       pydoc.classify_class_attrs(object))
        while attrs:
            if mro:
                thisclass = mro.popleft()
            else:
                thisclass = attrs[0][2]
            attrs, inherited = pydoc._split_list(attrs,
                                                 lambda t: t[2] is thisclass)

            if thisclass is pydoc.__builtin__.object:
                attrs = inherited
                continue
            elif thisclass is object:
                tag = "defined here"
            else:
                tag = "inherited from %s" % pydoc.classname(thisclass,
                                                            object.__module__)

            # Sort attrs by name.
            attrs.sort()

            # Pump out the attrs, segregated by kind.
            attrs = spill("Methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'method')
            attrs = spill("Class methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'class method')
            attrs = spill("Static methods %s:\n" % tag, attrs,
                          lambda t: t[1] == 'static method')
            attrs = spilldescriptors("Data descriptors %s:\n" % tag, attrs,
                                     lambda t: t[1] == 'data descriptor')
            attrs = spilldata("Data and other attributes %s:\n" % tag, attrs,
                              lambda t: t[1] == 'data')
            assert attrs == []
            attrs = inherited

        contents = '\n'.join(contents)
        if not contents:
            return title + '\n'
        return title + '\n' + \
            self.indent(pydoc.rstrip(contents), ' |  ') + '\n'

    def docroutine(self, object, name=None, mod=None, cl=None):
        """Produce text documentation for a function or method object."""

        realname = object.__name__
        name = name or realname
        note = ''
        skipdocs = 0
        prefix = ''
        if inspect.ismethod(object):
            imclass = object.im_class
            if cl:
                if imclass is not cl:
                    note = ' from ' + pydoc.classname(imclass, mod)
            else:
                if object.im_self is not None:
                    note = ' method of %s instance' % pydoc.classname(
                        object.im_self.__class__, mod)
                else:
                    note = ' unbound %s method' % pydoc.classname(imclass, mod)
            object = object.im_func
            prefix = '.'

        if name == realname:
            title = "(" + prefix + self.bold(realname)
        else:
            if (cl and realname in cl.__dict__ and
                    cl.__dict__[realname] is object):
                skipdocs = 1
            title = self.bold(name) + " -> (" + prefix + realname

        if inspect.isfunction(object):
            args, varargs, varkw, defaults = inspect.getargspec(object)
            argspec = inspect.formatargspec(
                args, varargs, varkw, defaults, formatvalue=self.formatvalue)

            argspec = fixup_argspec(argspec)

            if realname == '<lambda>':
                title = self.bold(name) + ' lambda '
                argspec = argspec[1:-1]  # remove parentheses
        else:
            argspec = ' ...)'
        decl = title + argspec + note

        if skipdocs:
            return decl + '\n'
        else:
            doc = pydoc.getdoc(object) or ''
            return decl + '\n' + \
                (doc and pydoc.rstrip(self.indent(doc)) + '\n')

pydoc.text = HyTextDoc()
pydoc.html = HyHTMLDoc()


def hydoc(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'name', nargs='?',
        help='''Show text documentation on something.
        [name] may be the name of a Hy
        keyword, topic, function, module, or package, or a dotted
        reference to a class or function within a module or module in
        a package.  If [name] contains a '/', it is used as the path to a
        Hy (or Python) source file to document. If [name] is 'keywords',
        'topics', or 'modules', a listing of these things is displayed.
        ''')

    parser.add_argument(
        '-k', dest='keyword',
        help='Search for a keyword in the synopsis of all available modules')

    parser.add_argument(
        '-p', dest='port',
        help='Start an HTTP server on the given port on the local machine.')

    parser.add_argument(
        "-w", action='store_true',
        help="""Write out the HTML documentation for a module to
        a file in the current directory.  If [name] contains a '/',
        it is treated as a filename; if it names a directory, documentation
        is written for all the contents.""")

    opts = parser.parse_args(args[1:])

    if opts.keyword:
        pydoc.apropos(opts.keyword)
        return 0

    if opts.port:
        port = int(opts.port)

        def starting(server):
            print("starting hydoc server on port: %d" % port)
            print("use Ctrl-C to kill the server")

        def stopping():
            print("stopping hydoc server")
        pydoc.serve(port, starting, stopping)
        return 0

    name = opts.name
    if os.path.isfile(name) and os.path.exists(name):
        basename = os.path.basename(name)
        modname, ext = os.path.splitext(basename)
        name = hy.importer.import_file_to_module(modname, name)

    if opts.w and name:
        pydoc.writedoc(name)
        return 0

    if name:
        pydoc.help(name)
    else:
        opts = parser.parse_args(["-h"])

    return 0


# entry point for cmd line script "hydoc"
def main():
    sys.exit(hydoc(sys.argv))
