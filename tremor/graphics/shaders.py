import configparser
from typing import List

from OpenGL.GL.shaders import ShaderCompilationError

from tremor.graphics.surfaces import Material
from tremor.graphics.uniforms import *
import re as regex

PROGRAMS: Dict[str, 'MeshProgram'] = {}

# object programs
def get_program(name: str) -> 'MeshProgram':
    try:
        return PROGRAMS[name]
    except ValueError:
        raise Exception(f'{name} is not a valid program name.')

def get_default_program() -> 'MeshProgram':
    return get_program('default')

def get_programs() -> List['MeshProgram']:
    return list(PROGRAMS.values())

def create_all_programs(filepath='data/shaders/programs.ini',
                        vertex_location: str = 'data/shaders/vertex',
                        fragment_location: str = 'data/shaders/fragment') -> None:
    # read the config file
    config_parser = configparser.ConfigParser()
    config_parser.read(filepath, encoding="UTF-8")
    out = {}
    for program in config_parser.sections():
        program_name = str(program)
        out[program_name] = {}
        for key in config_parser[program_name]:
            value = config_parser[program_name][key]
            out[program_name][key] = str(value)

    # read files, load programs
    unique_vertex_shaders = []
    unique_fragment_shaders = []
    for prog in out.values():
        if prog['vertex'] not in unique_vertex_shaders:
            unique_vertex_shaders.append(prog['vertex'])
        if prog['fragment'] not in unique_fragment_shaders:
            unique_fragment_shaders.append(prog['fragment'])

    # compile the shaders uniquely, so that we don't compile one more than once
    compiled_vertex_shaders = {}
    compiled_fragment_shaders = {}
    fragment_shader_inputs = {}
    for vertex_shader in unique_vertex_shaders:
        txt = open(f'{vertex_location}/{vertex_shader}.glsl', 'r').read()
        compiled_vertex_shaders[vertex_shader] = create_shader(GL_VERTEX_SHADER, txt)

    for fragment_shader in unique_fragment_shaders:
        txt = open(f'{fragment_location}/{fragment_shader}.glsl', 'r').read()
        fragment_shader_inputs[fragment_shader] = ShaderInput.from_shader_source(txt)
        compiled_fragment_shaders[fragment_shader] = create_shader(GL_FRAGMENT_SHADER, txt)

    # then go back through programs and query the compiled shaders
    # also query for shader inputs
    # then create the program
    for prog_name, prog in out.items():
        create_program(prog_name, compiled_vertex_shaders[prog['vertex']], compiled_fragment_shaders[prog['fragment']], fragment_shader_inputs[prog['fragment']])

    # delete the shaders
    for shad in list(compiled_vertex_shaders.values()) + list(compiled_fragment_shaders.values()):
        glDeleteShader(shad)


def create_shader(type, source) -> object:
    shader = glCreateShader(type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    status = glGetShaderiv(shader, GL_COMPILE_STATUS)
    if status == GL_FALSE:
        raise ShaderCompilationError(
            "Compilation failure for %s\n%s" % (str(type), glGetShaderInfoLog(shader).decode()))
    return shader


def create_program(name: str, compiled_vertex, compiled_fragment, inputs):
    PROGRAMS[name] = MeshProgram(name, compiled_vertex, compiled_fragment, inputs)

class ShaderInput:
    """
    MAGIC: see from_shader_source
    """
    @staticmethod
    def from_shader_source (shader_source:str) -> List['ShaderInput']:
        """
        METHODOLOGY of SHADER INPUTS
        Scraping Inputs from the Shaders Themselves

        what:
        given a shader source (a string, the literal program), scan through each line and find lines
        starting with 'uniform' (which is the only type of shader input),
        and ending with a comment starting with '//mat'
        uniform <type> <name>;//mat[:dependency1,dependency2,...,dependencyn]
        For example:
        uniform sampler2D texColor;//mat:t_texColor,textured

        how:
        this built-in comment syntax easily identifies the location of said material input by placing it DIRECTLY beside where it is.
        this method allows for easy parsing, by simply determining material inputs, their types and default values

        why:
        pros:
         - no need to retype input name or type anywhere
         - easily expands to higher-level shader compilation
         - easy to locate

        cons:
         - somewhat ambiguous and the format is arbitrary
         - a little hacky
         - all in all seems a bit distasteful
        """
        lines = shader_source.split('\n')
        uniforms = []
        for l in lines:
            if l[:len('uniform')] == 'uniform':
                uniforms.append(l)
        inputs = []
        find_input = regex.compile(r'uniform\s(\w+)\s(\w+);//mat(?::([\w\d,_]+))?')
        for u in uniforms:
            m = find_input.match(u)
            if m is not None:
                inputs.append(m.groups())

        # convert inputs into shader inputs : [type, name, [dependencies]]
        shader_inputs = []
        for i in inputs:
            typ = i[0]
            name = i[1]
            depend = []
            if len(i)>2:
                depend = i[2].split(',')

            is_texture = False
            if typ in u_type_default_args:
                default_args = u_type_default_args[typ]
            else:
                default_args = []
            if typ in u_type_default_value_args:
                default_value = u_type_default_value_args[typ]
            else:
                default_value = [0]
                if typ=='sampler2D':
                    is_texture=True
            shader_inputs.append(ShaderInput(name, typ, default_args, default_value, is_texture, depend))
        return shader_inputs
    def __init__ (self, name:str, u_type='float', default_args=[], value:list=[0.0], is_texture=False, dependencies:List[str]=[]):
        self.name = name
        self.u_type = u_type
        self.default_args = default_args # arguments for a glUniform call that precede the actual value
        self._value = value # the actual value of the uniform
        self.is_texture = is_texture # in the case where this is true, the name is the same as the MaterialTexture type flag.
            # @see: MaterialTexture.COLOR for example. If it isn't, it will throw a KeyError in MeshShader
        self.dependencies = dependencies # dependencies are the #define directives that are required for this material property.
            # they are to signal if they're in an #ifdef of some sort or whatnot, that way with different shader compilations they can be removed
        self.texture_type = None
        if self.is_texture:
            self.texture_type = self.name
    def set_value (self, value):
        if len(self._value)==1:
            self._value = [value]
        else:
            self._value = value
    def get_value (self):
        if len(self._value)==1:
            return self._value[0]
        else:
            return self._value
    value = property(get_value, set_value)
    def get_uniform_args (self) -> list:
        return self.default_args + self._value

    """
    If one input is defined in a vertex shader, and one is defined in a fragment shader,
    or the same name is defined in two shaders, then the ShaderInput representing that single uniform
    is the two inputs together with the MAXIMUM of restraints of both
    """
    @staticmethod
    def combine_inputs (a:'ShaderInput', b:'ShaderInput') -> 'ShaderInput':
        # everything should be the same about them other than DEPENDENCIES
        # in that case, take every non-duplicate dependency and put them in the same list
        adep = a.dependencies
        bdep = b.dependencies
        dep = [a for a in adep]
        for b in bdep:
            if not b in dep:
                dep.append(b)
        return ShaderInput(a.name, a.u_type, a.default_args, a._value, a.is_texture, dep)

class MeshProgram:
    def __init__(self, name: str, compiled_vertex, compiled_fragment, inputs:List[ShaderInput]=[]):
        self.name = name
        self.program = glCreateProgram()
        self.uniforms:Dict[str, Uniform] = {}
        self.inputs:List[ShaderInput] = inputs
        self.add_uniforms_from_inputs()

        glAttachShader(self.program, compiled_vertex)
        glAttachShader(self.program, compiled_fragment)
        glLinkProgram(self.program)
        status = glGetProgramiv(self.program, GL_LINK_STATUS)
        if status == GL_FALSE:
            print("Linker failure: " + str(glGetProgramInfoLog(self.program)))

    def add_uniforms_from_inputs (self):
        for i in self.inputs:
            if not self.check_is_uniform(i.name) and not i.is_texture:
                self.add_uniform(i.name, i.u_type)

    def add_uniform (self, name: str, u_type: str):
        if not u_type in u_types.keys():
            raise Exception(f'uniform type {u_type} is not a valid type')

        self.uniforms[name] = Uniform(
            name=name,
            loc=None,
            values=[],
            u_type=u_type
        )

    def update_uniform(self, name: str, values: list = None):
        glUseProgram(self.program)
        self.check_is_uniform(name)
        self.uniforms[name].call_uniform_func(values)

    def init_uniforms(self):
        glUseProgram(self.program)
        for n, u in self.uniforms.items():
            u.loc = glGetUniformLocation(self.program, u.name)

    def check_is_uniform(self, name: str) -> bool:  # not a hard stop, but warning
        if not name in self.uniforms:
            # print('%s is not a uniform!' % name)
            return False
        return True

    def set_uniform_values(self, name: str, values: list):
        self.check_is_uniform(name)
        self.uniforms[name].values = values

    def get_uniform_values (self, name: str):
        if not self.check_is_uniform(name): print(f'{name} is not a uniform!')
        return self.uniforms[name].values

    # get a material with relevant properties for this shader
    def create_material (self, name=None) -> Material:
        if name is None:
            name = f'{self.name}_mat'
        mat = Material(name)
        for prop in self.inputs:
            if prop.is_texture: continue # don't set default textures, because empty textures are created in Material.__init__
            mat.set_property(prop.name, prop.value)
        return mat

    # set uniforms for this shader from the provided material that are relevant
    def use_material (self, mat:Material):
        for inp in self.inputs:
            if inp.is_texture:
                mat_tex = mat.get_mat_texture(inp.texture_type)
                glUniform1i(
                    glGetUniformLocation(self.program, mat_tex.tex_type),
                    mat_tex.texture.index
                )
            else:
                inp.set_value(mat.get_property(inp.name))
                self.update_uniform(inp.name, inp.get_uniform_args())

class ShaderPackage:
    """
    This class can spawn a MeshProgram
    """
    def __init__ (self, compiled_shader, shader_inputs):
        self.compiled_shader = compiled_shader
        self.shader_inputs = shader_inputs

    @staticmethod
    def create_mesh_program (vertex_shader_package:'ShaderPackage', fragment_shader_package: 'ShaderPackage', name:str) -> MeshProgram:
        inputs = []

        # merge the inputs

        # seed with vertex inputs
        for inp in vertex_shader_package.shader_inputs:
            ninp = inp
            for i in fragment_shader_package.shader_inputs:
                if i.name == inp.name: # deal with duplicates
                    ninp = ShaderInput.combine_inputs(i, inp)
                    break
            inputs.append(ninp)

        # then seed with fragment inputs
        for inp in fragment_shader_package.shader_inputs:
            append = True
            for i in inputs:
                if i.name == inp.name: # duplicates already dealt with
                    append = False
                    break
            if append:
                inputs.append(inp)
        return MeshProgram(name, vertex_shader_package.compiled_shader, fragment_shader_package.compiled_shader, inputs)

class FlaggedShader:
    """
    MAGIC: this description
    This is a class not containing DIFFERENT shaders, just different compilations of ONE shader.
    This class relies on the use of `#define [var]` in a shader to introduce branching.
    This branching is characterized at compile time in this class.
    This class can spawn a ShaderPackage
    """
    @staticmethod
    def from_shader_source (frag_source:str, shader_type) -> 'FlaggedShader':
        expr_define = regex.compile(r'#define\s+([_\w]+)\s*$')
        expr_ver = regex.compile(r'#version\s+(\d+)\s*$')
        lines = frag_source.split('\n')
        flags = []
        version = None
        for l in lines:
            v = expr_ver.match(l)
            if v is not None:
                version = v.groups()[0]
                continue
            m = expr_define.match(l)
            if m is not None:
                flags.append(m.groups()[0])
                lines.remove(l)

        root_src = '\n'.join(lines)
        if version is None:
            raise Exception('Could not determine version of shader.')
        return FlaggedShader(flags, root_src, version, shader_type)

    def __init__ (self, flags:List[str], root_source:str, version:str, shader_type):
        self.flag_list = flags
        self.shader_type = shader_type
        self.version = version
        self.root_src = root_source
        self.compiled_shaders = [] # this is indexed by state
        self.shader_inputs:List[ShaderInput] = [] # this is for ALL possible shaders coming from this shader
        self.flags = FlaggedStates(self.flag_list)
        self.compile_shaders()

    def flag (self, flag) -> int:
        if not self.flags.has_flag(flag):
            raise Exception(f"{flag} is not a valid flag for this shader.")
        else:
            return self.flags[flag]

    def get_shader_from_state (self, state:int):
        return self.compiled_shaders[state]

    def get_shader_from_flags (self, *flags:List[str]):
        return self.compiled_shaders[self.flags.combine_flags(*flags)]

    def compose_shader_src (self, state:int) -> str:
        flags = self.flags.decompose_state(state)
        defines = ""
        if len(flags)>0:
            defines = "#define " + "\n#define".join(flags)
        return f"#version {self.version}\n" + defines + f"\n{self.root_src}"

    def compile_shaders (self):
        self.shader_inputs = ShaderInput.from_shader_source(self.root_src)
        self.compiled_shaders = []
        for i in range(self.flags.num_states()):
            src = self.compose_shader_src(i)
            self.compiled_shaders.append(create_shader(self.shader_type, src))

    def weeded_inputs (self, state:int) -> List[ShaderInput]: # create a list of ShaderInputs to include for a shader of this state
        defined = self.flags.decompose_state(state)
        valid_inputs = []
        for inp in self.shader_inputs:
            valid = True
            for dep in inp.dependencies:
                if not dep in defined:
                    valid = False
                    break
            if valid:
                valid_inputs.append(inp)
        return valid_inputs

    def spawn_shader_package (self, state:int) -> ShaderPackage:
        return ShaderPackage(self.compiled_shaders[state], self.weeded_inputs(state))

    def spawn_all_shader_packages (self) -> List[ShaderPackage]:
        return [self.spawn_shader_package(state) for state in range(self.flags.num_states())]


class BranchedProgram:
    """
    This class uses a FlaggedShader for a VERTEX and FRAGMENT shader
    It compiles every program for every branched combination of the two together
    """
    def __init__ (self, name:str, flagged_vertex:FlaggedShader, flagged_fragment:FlaggedShader):
        self.name = name
        self.flagged_vertex = flagged_vertex
        self.flagged_fragment = flagged_fragment
        self.programs = [] # indexed by binary combination (not superposition) of vertex and fragment states
            # for example, vertex has 3 flags, fragment has 8 flags
            # 0 0 0   0 0 0 0 0 0 0 0

        frag_shad = self.flagged_fragment.spawn_all_shader_packages()
        vert_shad = self.flagged_vertex.spawn_all_shader_packages()
        for v_flag in range(self.flagged_vertex.flags.num_states()):
            for f_flag in range(self.flagged_fragment.flags.num_states()):
                self.programs.append(ShaderPackage.create_mesh_program(vert_shad[v_flag], frag_shad[f_flag], name))

    def get_program (self, vertex_state:int, fragment_state:int) -> MeshProgram:
        v_state = vertex_state << self.flagged_fragment.flags.num_flags()
        return self.programs[v_state|fragment_state] # should be the same as + if I did it right

    def get_program_from_flags (self, vertex_flags:List[str], fragment_flags:List[str]):
        v_state = self.flagged_vertex.flags.combine_flags(vertex_flags)
        f_state = self.flagged_fragment.flags.combine_flags(fragment_flags)
        return self.get_program(v_state, f_state)

class FlaggedStates:
    """
    convention: a 'state' is a combination of flags, ex. 1001
                a 'flag' represents a single positive state at a bit position (int), for example RANDOM_FLAG = 0100 = 4
    """
    def __init__ (self, states:List[str]):
        self._flags = states
        self._num_states = 2 ** len(self._flags)
        self._keyed_flags:Dict[str, int] = {}
        index = -1
        for s in self._flags:
            index += 1
            setattr(self, s, 2 ** index)
            self._keyed_flags[s] = 2 ** index

    def decompose_state (self, state:int) -> List[str]: # flags
        include = []
        for i in range(len(self._flags)):
            if state>>i&1:
                include.append(self._flags[i])
        return include

    def combine_flags (self, *args:List[str]) -> int: # state
        i = 0
        for a in args:
            i |= self[a]
        return i

    def has_flag (self, flag) -> bool:
        return flag in self._flags

    def num_states(self) -> int:
        return self._num_states

    def num_flags(self) -> int:
        return len(self._flags)

    def get_value (self, flag) -> int:
        if flag in self._flags:
            return self._keyed_flags[flag]
        else:
            raise Exception(f'{flag} is not a valid state in this set.')

    def __getitem__ (self, item):
        return self.get_value(item)
