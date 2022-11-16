'''
Interface for PySCF and ASE
'''

from ase.calculators.calculator import Calculator
from ase.units import Bohr, Hartree
from pyscf.data import nist
from pyscf import neo
from pyscf import gto, dft
from pyscf.scf.hf import dip_moment
from pyscf.lib import logger

# from examples/scf/17-stability.py
def stable_opt_internal(mf):
    log = logger.new_logger(mf)
    if hasattr(mf, 'mf_elec'):
        mf_elec = mf.mf_elec
    else:
        mf_elec = mf
    mo1, _, stable, _ = mf_elec.stability(return_status=True)
    cyc = 0
    while (not stable and cyc < 10):
        log.note('Try to optimize orbitals until stable, attempt %d' % cyc)
        dm1 = mf_elec.make_rdm1(mo1, mf_elec.mo_occ)
        mf = mf.run(dm1)
        mo1, _, stable, _ = mf_elec.stability(return_status=True)
        cyc += 1
    if not stable:
        log.note('Stability Opt failed after %d attempts' % cyc)
    return mf

class Pyscf_NEO(Calculator):

    implemented_properties = ['energy', 'forces', 'dipole']
    default_parameters = {'basis': 'ccpvdz',
                          'charge': 0,
                          'spin': 0,
                          'xc': 'b3lyp',
                          'quantum_nuc': ['H'],
                          'atom_grid' : None}


    def __init__(self, **kwargs):
        Calculator.__init__(self, **kwargs)

    def calculate(self, atoms=None, properties=['energy', 'forces', 'dipole'],
                  system_changes=['positions', 'numbers', 'cell', 'pbc', 'charges', 'magmoms']):
        Calculator.calculate(self, atoms, properties, system_changes)
        mol = neo.Mole()
        atoms = self.atoms.get_chemical_symbols()
        ase_masses = self.atoms.get_masses()
        positions = self.atoms.get_positions()
        atom_pyscf = []
        for i in range(len(atoms)):
            if atoms[i] == 'Mu':
                atom_pyscf.append(['H@0', tuple(positions[i])])
            elif atoms[i] == 'D':
                atom_pyscf.append(['H+%i' %i, tuple(positions[i])])
            elif atoms[i] == 'H' and abs(ase_masses[i]-2.014) < 0.01:
                # this is for person who does not want to modify ase
                # by changing the mass array, pyscf still accepts H as D
                atom_pyscf.append(['H+%i' %i, tuple(positions[i])])
            else:
                atom_pyscf.append(['%s%i' %(atoms[i],i), tuple(positions[i])])
        mol.build(quantum_nuc = self.parameters.quantum_nuc,
                  atom = atom_pyscf,
                  basis = self.parameters.basis,
                  charge = self.parameters.charge, spin = self.parameters.spin)
        if self.parameters.spin == 0:
            mf = neo.CDFT(mol)
        else:
            mf = neo.CDFT(mol, unrestricted = True)
        mf.mf_elec.xc = self.parameters.xc
        if self.parameters.atom_grid is not None:
            mf.mf_elec.grids.atom_grid = self.parameters.atom_grid
        # check stability for UKS
        mf.scf()
        if self.parameters.spin !=0:
            mf = stable_opt_internal(mf)
        self.results['energy'] = mf.e_tot*Hartree
        g = mf.Gradients()
        self.results['forces'] = -g.grad()*Hartree/Bohr

        dip_elec = dip_moment(mol.elec, mf.mf_elec.make_rdm1()) # dipole of electrons and classical nuclei
        dip_nuc = 0
        for i in range(len(mf.mf_nuc)):
            ia = mf.mf_nuc[i].mol.atom_index
            dip_nuc += mol.atom_charge(ia) * mf.mf_nuc[i].nuclei_expect_position * nist.AU2DEBYE

        self.results['dipole'] = dip_elec + dip_nuc


class Pyscf_DFT(Calculator):

    implemented_properties = ['energy', 'forces', 'dipole']
    default_parameters = {'mf':'RKS',
                          'basis': 'ccpvdz',
                          'charge': 0,
                          'spin': 0,
                          'xc': 'b3lyp',
                          'atom_grid' : None,
                         }


    def __init__(self, **kwargs):
        Calculator.__init__(self, **kwargs)

    def calculate(self, atoms=None, properties=['energy', 'forces', 'dipole'],
                  system_changes=['positions', 'numbers', 'cell', 'pbc', 'charges', 'magmoms']):
        Calculator.calculate(self, atoms, properties, system_changes)
        mol = gto.Mole()
        atoms = self.atoms.get_chemical_symbols()
        positions = self.atoms.get_positions()
        atom_pyscf = []
        for i in range(len(atoms)):
            if atoms[i] == 'D':
                atom_pyscf.append(['H+', tuple(positions[i])])
            else:
                atom_pyscf.append(['%s' %(atoms[i]), tuple(positions[i])])
        mol.build(atom = atom_pyscf, basis = self.parameters.basis,
                  charge = self.parameters.charge, spin = self.parameters.spin)
        if self.parameters.spin != 0:
            mf = dft.UKS(mol)
        else:
            mf = dft.RKS(mol)
        mf.xc = self.parameters.xc
        if self.parameters.atom_grid is not None:
            mf.grids.atom_grid = self.parameters.atom_grid
        # check stability for UKS
        mf.scf()
        if self.parameters.spin !=0:
            mf = stable_opt_internal(mf)
        self.results['energy'] = mf.e_tot*Hartree
        g = mf.Gradients()
        self.results['forces'] = -g.grad()*Hartree/Bohr
        self.results['dipole'] = dip_moment(mol, mf.make_rdm1())
