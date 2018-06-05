#!/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Randomly explorer IFS function

* TODO: add automatic evaluation of the result:
** check for color distribution of different c value
** check for smooth variation when c or mod changes
"""

import copy
import random


class FormulaTree:
    def __init__(self):
        self.right = None
        self.left = None
        self.operation = None


def generate():
    """This return valid opencl code:

    >>> generate()
    "z = cdouble_divider(cdouble_tan(cdouble_divider(cdouble_mul(c, z), mod)),
                        4.901648073450788) ;"

    >>> generate()
    "z = cdouble_fabs(cdouble_exp(cdouble_sub(z, c)));"
    """
    root = FormulaTree()

    operations = ["pow", "mul", "add", "sub", "divide"]
    root.operation = random.choice(operations)
    for i in ("add", "sub"):
        # Increase odd of using add or sub
        for w in range(1):
            operations.append(i)

    values = ["z", "c"]  # , "d", "mod1", "mod2"]
    transformation = [
        "iabs", "rabs", "fabs", "log", "exp", "cos", "sin", "tan"]
    operations.extend(transformation)

    root.right = random.choice(values)
    root.left = random.choice(values)

    for op in range(random.randint(2, 17)):
        node = FormulaTree()
        node.operation = random.choice(operations)
        v = copy.copy(values)
        if node.operation in ("pow", "mul", "add", "divide"):
            # These operations can use real value
            v.append("mod")
            v.append("const")
        random.shuffle(v)
        if node.operation in transformation:
            node.left = None
            node.right = root
        elif random.randint(0, 1):
            node.left = root
            node.right = v.pop()
            if node.right in ("mod", "const"):
                node.operation = node.operation + "r"
            if node.right == "const":
                node.right = str(random.random() * random.randint(0, 10))
        else:
            node.right = root
            node.left = v.pop()
            if node.left in ("mod", "const"):
                node.operation = "r" + node.operation
            if node.left == "const":
                node.left = str(random.random() * random.randint(0, 10))
        root = node

    def render_opencl(tree):
        s = []
        s.append("cdouble_" + tree.operation + "(")
        if isinstance(tree.left, FormulaTree):
            s.extend(render_opencl(tree.left))
            s.append(", ")
        elif tree.left is not None:
            s.append(tree.left)
            s.append(", ")
        #    if tree.left is None:
        #        s.append("(")
        if isinstance(tree.right, FormulaTree):
            s.extend(render_opencl(tree.right))
        else:
            s.append(tree.right)
        s.append(") ")
        return s

    return ("z = " + "".join(render_opencl(root)) + ";")


def main():
    import subprocess
    try:
        while True:
            argv = ["./explorer_complex.py", "--size", "3",
                    "complex_parameters/quack.yaml",
                    '{"formula": "%s"}' % generate()]
            subprocess.Popen(argv).wait()
    except KeyboardInterrupt:
        pass

main()
