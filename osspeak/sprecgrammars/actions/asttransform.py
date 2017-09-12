'''
Replace ast.Name nodes with strings wherever possible:
    foo + bar -> 'foo' + 'bar'
    sorted([sjhsdfjsdfsdf, abc, 'de'], key=len) -> sorted(['de', 'abc', 'sjhsdfjsdfsdf'], key=len)

Ignore:
    foo[0], foo[::], foo()
    arguments TODO: fix scope escaping
    locals/globals unless they're direct children of root expression
'''

import ast
from sprecgrammars.functions import library


class NameToStringTransformer(ast.NodeTransformer):

    def __init__(self, root, namespace, arguments):
        super().__init__()
        self.namespace = namespace
        self.arguments = arguments
        self.nodes_to_replace = self.to_replace(root)
        
    def to_replace(self, root):
        nodes_to_replace = set()
        names_to_keep = set()
        for node in ast.walk(root):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.arg):
                    names_to_keep.add(child.arg)
                if not isinstance(child, ast.Name):
                    continue
                if child.id in self.arguments:
                    names_to_keep.add(child.id)
                    continue
                is_call_or_slice = isinstance(node, (ast.Subscript, ast.Attribute)) or (isinstance(node, ast.Call) and node.func is child)
                if not (is_call_or_slice or 
                    (child.id in self.namespace and node is not root)):
                    nodes_to_replace.add(child)
        return set(n for n in nodes_to_replace if n.id not in names_to_keep)

    def visit_Name(self, node):
        if node in self.nodes_to_replace:
            return ast.Str(s=node.id)
        return node

class SetLiteralTransformer(ast.NodeTransformer):

    def __init__(self):
        super().__init__()
        
    def visit_Set(self, node):
        func = ast.Name(id='keys', ctx=ast.Load())
        return ast.Call(func=func, args=node.elts, keywords=[])

class ATransformer(ast.NodeTransformer):

    def __init__(self):
        super().__init__()
        
    def visit_Call(self, node):
        func = ast.Name(id='keys', ctx=ast.Load())
        path = node_path(node.func)
        if path in library.lambda_arguments:
            newargs = []
            for arg in node.args:
                largs = ast.arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
                newarg = ast.Lambda(args=largs, body=arg)
                newargs.append(newarg)
            node.args = newargs
        return node

class VariableArgumentTransformer(ast.NodeTransformer):

    def __init__(self, root):
        super().__init__()
        self.build_parent_map = self.build_parent_map(root)
        
    def visit_Call(self, node):
        if node_path(node.func) != ('result', 'vars', 'get'):
            return node
        # keywords = [keyword(arg='a', value=NameConstant(value=True))]
        return node
        return node

    def build_parent_map(self, root):
        parent_map = {root: None}
        for node in ast.walk(root):
            for child in ast.iter_child_nodes(node):
                parent_map[child] = node
        return parent_map

    def get_containing_function(self, node):
        while node:
            

def node_path(node):
    if isinstance(node, ast.Name):
        return node.id,
    return node_path(node.value) + (node.attr,)

def transform_expression(expr_text, namespace=None, arguments=None):
    arguments = arguments or []
    namespace = get_builtins() if namespace is None else namespace
    expr = ast.parse(expr_text, mode='eval')
    new_expr = NameToStringTransformer(expr, namespace, arguments).visit(expr)
    new_expr = SetLiteralTransformer().visit(new_expr)
    new_expr = ATransformer().visit(new_expr)
    new_expr = VariableArgumentTransformer(new_expr).visit(new_expr)
    return compile(ast.fix_missing_locations(new_expr), filename=f'<{expr_text}>', mode='eval')

def get_builtins():
    return __builtins__ if isinstance(__builtins__, dict) else dir(__builtins__)