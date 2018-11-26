from __future__ import absolute_import
from manage_crystal import Crys
import numpy as np
from six.moves import range


def parse_axsf(file):
    ''' Parse .axsf and .xsf files and return a Crys object '''
    c = Crys()
    while True:
        if file.readline().split()[0] == 'PRIMVEC':
            break
    for i in range(3):
        data = file.readline().split()
        for j in range(3):
            c.matrix[i][j] = data[j]
    while True:
        if file.readline().split()[0] == 'PRIMCOORD':
            break
    c.natoms = int(file.readline().split()[0])
    for i in range(c.natoms):
        data = file.readline().split()
        # The atom type can be given as element or atomic number
        if is_number(data[0]):
            c.atom_type.append(atomic_symbol[data[0]])
        else:
            c.atom_type.append(data[0])
        c.atom_xyz.append([float(data[1]), float(data[2]), float(data[3])])
    return c


def parse_cif(file):
    ''' Parse .cif file and return a Crys object '''
    # REQUIREMENTS:
    # - only valid for P1 symmetry
    # - cell data should be specified before the atom data
    # - if some other "_atom_something" are specified before, it does not work
    # - after the atom coordinates it breaks with "loop_" or EOF
    c = Crys()
    while True:
        line = file.readline()
        data = line.split()
        if line == "":
            break
        if len(data) > 0 and (data[0] == "_cell_length_a"):
            c.length[0] = float(data[1])
        if len(data) > 0 and (data[0] == "_cell_length_b"):
            c.length[1] = float(data[1])
        if len(data) > 0 and (data[0] == "_cell_length_c"):
            c.length[2] = float(data[1])
        if len(data) > 0 and (data[0] == "_cell_angle_alpha"):
            c.angle_deg[0] = float(data[1])
        if len(data) > 0 and (data[0] == "_cell_angle_beta"):
            c.angle_deg[1] = float(data[1])
        if len(data) > 0 and (data[0] == "_cell_angle_gamma"):
            c.angle_deg[2] = float(data[1])
        # if the "_atom_site_***" section starts, remember the order
        if len(data) > 0 \
           and len(data[0].split("_")) > 1 \
           and data[0].split("_")[1] == "atom":
            data_order_dic = {}
            order = 0
            while len(data[0].split("_")) > 1 \
                  and data[0].split("_")[1] == "atom":
                data_order_dic[data[0]] = order
                line = file.readline()
                data = line.split()
                order += 1
            break  #go in the loop to read coordinates
    # Read atomic element, coordinates and charges
    while True:
        if line == "" \
           or line =="\n" \
           or data[0] == "loop_" \
           or data[0] == "_loop":
            break
        # looks for "type_symbol" before and, if missing for "label"
        if "_atom_site_type_symbol" in data_order_dic:
            c.atom_type.append(data[data_order_dic["_atom_site_type_symbol"]])
        elif "_atom_site_label" in data_order_dic:
            c.atom_type.append(data[data_order_dic["_atom_site_label"]])
        else:
            sys.exit("EXIT: in cif missing type_symbol and label")
        if "_atom_site_fract_x" in data_order_dic:
            c.atom_fract.append([
                float(data[data_order_dic["_atom_site_fract_x"]]),
                float(data[data_order_dic["_atom_site_fract_y"]]),
                float(data[data_order_dic["_atom_site_fract_z"]]),
            ])
        elif "_atom_site_Cartn_x" in data_order_dic:
            c.atom_xyz.append([
                float(data[data_order_dic["_atom_site_Cartn_x"]]),
                float(data[data_order_dic["_atom_site_Cartn_y"]]),
                float(data[data_order_dic["_atom_site_Cartn_z"]]),
            ])
        else:
            sys.exit("EXIT: in cif missing fract_ and Cartn_ coordinates")
        if "_atom_site_charge" in data_order_dic:
            c.atom_charge.append(
                float(data[data_order_dic["_atom_site_charge"]]))
        line = file.readline()
        data = line.split()
    return c


def parse_cp2k(file):
    ''' Parse any CP2K input file and return a Crys object '''
    while True:
        data = file.readline().split()
        cell_dict = {"A": 0, "B": 1, "C": 2}
        if len(data) > 0 and data[0] in cell_dict:
            if data[1][0] != "[":  # No unit specified. Default: Angstrom.
                shift = 0
            elif data[1].lower() == "[angstrom]":
                shift = 1
            else:
                sys.exit("WARNING: in parsing CP2K, weird units. EXIT")
            for i in range(3):
                c.inp_matrix[cell_dict[data[0]]][i] = data[1 + i + shift]

        if len(data) > 0 and (data[0] == "&COORD"):
            break
    scaled_coord = False  #Default
    while True:
        data = file.readline().split()
        if data[0] == "SCALED" \
         and data[1].lower() in ["t", "true", ".true."]:
            scaled_coord = True
        elif data[0] == "SCALED" \
         and data[1].lower() in ["f", "false", ".false."]:
            scaled_coord = False
        elif data[0] == "&END":  # End of &COORD section
            break
        elif len(data) > 0:
            c.atom_type.append(data[0])
            if scaled_coord:
                c.atom_fract.append(
                    [float(data[1]),
                     float(data[2]),
                     float(data[3])])
            else:
                c.atom_xyz.append(
                    [float(data[1]),
                     float(data[2]),
                     float(data[3])])
    return c


def parse_cssr(file):
    ''' Parse .cssr file and return a Crys object '''
    # File format description: http://www.chem.cmu.edu/courses/09-560/docs/msi/modenv/D_Files.html#944777
    c = Crys()
    data = file.readline().split()
    c.length = [float(data[0]), float(data[1]), float(data[2])]
    data = file.readline().split()
    c.angle_deg = [float(data[0]), float(data[1]), float(data[2])]
    c.natoms = int(file.readline().split()[0])
    junk = file.readline()
    for i in range(c.natoms):
        data = file.readline().split()
        c.atom_type.append(data[1])
        c.atom_fract.append([float(data[2]), float(data[3]), float(data[4])])
        if len(data) == 14:
            c.atom_charge.append(float(data[13]))
    return c


def parse_cube(file):
    ''' Parse .cube file and return a Crys object '''
    c = Crys()
    junk = file.readline()  #header1
    junk = file.readline()  #header2
    data = file.readline().split()
    c.natoms = int(data[0])
    for i in range(3):
        data = file.readline().split()
        for j in range(3):
            c.matrix[i][j] = float(data[0]) * float(data[j]) / ANGS2BOHR
    for i in range(c.natoms):
        data = file.readline().split()
        c.atom_type.append(atomic_symbol[int(data[0])])
        c.atom_xyz.append([
            float(data[2]) / ANGS2BOHR,
            float(data[3]) / ANGS2BOHR,
            float(data[4]) / ANGS2BOHR
        ])
    return c


def parse_pdb(file):
    ''' Parse .pdb file and return Crys object '''
    c = Crys()
    while True:
        line = file.readline()
        data = line.split()
        if line == "":
            break
        elif len(data) > 0 and (data[0] == 'END' or data[0] == 'ENDMDL'):
            break
        elif len(data) > 0 and data[0] == 'CRYST1':
            c.length = [
                float(line[0o6:15]),
                float(line[15:24]),
                float(line[24:33])
            ]
            c.angle_deg = [
                float(line[33:40]),
                float(line[40:47]),
                float(line[47:54])
            ]
        elif len(data) > 0 and (data[0] == "ATOM" or data[0] == "HETATM"):
            c.atom_type.append(data[2])  #maybe read to data[-1]
            c.atom_xyz.append(
                [float(line[30:38]),
                 float(line[38:46]),
                 float(line[46:54])])
    return c


def parse_poscar(file):
    ''' Parse Vasp's POSCAR file and return a Crys object '''
    c = Crys()
    junk_title = file.readline()
    junk_symm = file.readline()
    for i in range(3):
        data = file.readline().split()
        for j in range(3):
            c.matrix[i][j] = float(data[j])
    poscar_atomtypes = file.readline().split()
    poscar_atomnumbers = file.readline().split()
    for i in range(len(poscar_atomtypes)):
        for j in range(int(poscar_atomnumbers[i])):
            c.atom_type.append(poscar_atomtypes[i])
    c.natom = len(c.atom_type)
    coord_type = file.readline().split()[0]
    if coord_type.lower() == 'direct':
        for i in range(c.natoms):
            data = file.readline().split()
            c.atom_fract.append(
                [float(data[0]),
                 float(data[1]),
                 float(data[2])])
    elif coord_type.lower() == 'cartesian':
        for i in range(c.natoms):
            data = file.readline().split()
            c.atom_xyz.append([float(data[0]), float(data[1]), float(data[2])])
    return c


def parse_pwo(file):
    ''' Parse Quantum Espresso's .pwo and .pwi files and return Crys object '''
    c = Crys()
    # Parse cell:
    # search for the last time the cell/coord are printed and jump to that
    # line (no need to be converged). ONLY if they are not found, it reads the
    # initial input cell
    with file as myFile:
        for num, line in enumerate(myFile, 1):
            if 'CELL_PARAMETERS' in line:
                cell_line = num
    file.seek(0)
    if 'cell_line' in locals():  #read cell in vc-relax calculation
        for i in range(0, cell_line):
            skip = file.readline()  #title line
        for i in range(3):
            data = file.readline().split()
            for j in range(3):
                c.matrix[i][j] = float(data[j])
    else:  #read cell in scf or relax calculation
        while True:
            data = file.readline().split()
            if len(data) > 0 and (data[0] == "celldm(1)="):
                celldm1 = float(data[1]) / ANGS2BOHR
                skip = file.readline().split()
                skip = file.readline().split()
                skip = file.readline().split()
                for i in range(3):
                    data = file.readline().split()
                    for j in range(3):
                        c.matrix[i][j] = float(data[3 + j]) * celldm1
                break
    file.seek(0)
    # Parse atomic coordinates
    with file as myFile:
        for num, line in enumerate(myFile, 1):
            if 'ATOMIC_POSITIONS' in line:
                atomic_line = num
                if line.split()[1] == 'angstrom' \
                 or line.split()[1] == '(angstrom)':
                    readfractional = False
                elif line.split()[1] == 'crystal' \
                 or line.split()[1] == '(crystal)':
                    readfractional = True
    file.seek(0)
    if 'atomic_line' in locals():  #read atomic in vc-relax and relax calc.
        for i in range(0, atomic_line):
            skip = file.readline()
        i = 0
        while True:
            data = file.readline().split()
            if len(data) < 4:  #if the coordinates are finished, break
                break
            else:
                c.atom_type.append(data[0])
                if readfractional:
                    c.atom_fract.append(
                        [float(data[1]),
                         float(data[2]),
                         float(data[3])])
                else:
                    c.atom_xyz.append(
                        [float(data[1]),
                         float(data[2]),
                         float(data[3])])
    else:  #read atomic in scf calculation
        while True:
            data = file.readline().split()
            if len(data) > 0 and (data[0] == "celldm(1)="):
                celldm1 = float(data[1]) / ANGS2BOHR
            if len(data) > 3 and (data[3] == "positions"):
                while True:
                    data = file.readline().split()
                    if len(data) < 10:  #if the file is finished stop
                        break
                    else:
                        c.atom_type.append(data[1])
                        c.atom_xyz.append(
                            [float(data[6]),
                             float(data[7]),
                             float(data[8])])
                break
    return c


def parse_xyz(file):
    ''' Parse .xyz file and return Crys object '''
    c = Crys()
    c.natoms = int(file.readline().split()[0])
    data = file.readline().split()
    if len(data) >= 7 and data[0] == 'CELL:':
        c.length = [float(data[1]), float(data[2]), float(data[3])]
        c.angle_deg = [float(data[4]), float(data[5]), float(data[6])]
    elif len(data) >= 10 and data[0] == 'cell:':
        c.matrix[0] = [float(data[1]), float(data[2]), float(data[3])]
        c.matrix[0] = [float(data[4]), float(data[5]), float(data[6])]
        c.matrix[0] = [float(data[7]), float(data[8]), float(data[9])]
    elif len(data) >= 23 and data[0] == 'jmolscript:':
        c.matrix[0] = [float(data[10]), float(data[11]), float(data[12])]
        c.matrix[0] = [float(data[15]), float(data[16]), float(data[17])]
        c.matrix[0] = [float(data[20]), float(data[21]), float(data[22])]
    for i in range(c.natoms):
        data = file.readline().split()
        c.atom_type.append(data[0])
        c.atom_xyz.append([float(data[1]), float(data[2]), float(data[3])])
        if len(data) == 5:  # if there is an extra column read it as charge
            c.atom_charge.append(float(data[4]))
    return c


def parse_xyz_tm3(file):
    ''' Parse .xyz file (tailor made #3) and return Crys object '''
    c = Crys()
    junk = file.readline()  #the first line has the filename
    data = file.readline().split()
    c.length = [float(data[1]), float(data[2]), float(data[3])]
    ac.angle_deg = [float(data[4]), float(data[5]), float(data[6])]
    c.natoms = int(file.readline().split()[0])
    for i in range(c.natoms):
        data = file.readline().split()
        c.atom_type.append(data[0])
        c.atom_fract.append([float(data[1]), float(data[2]), float(data[3])])
        if len(data) > 4:  # if not, the Qeq method crashed: no charge
            charge.append(float(data[5]))
    return c