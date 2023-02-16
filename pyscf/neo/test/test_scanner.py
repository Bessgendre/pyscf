#!/usr/bin/env python

import unittest
import numpy
from pyscf import neo
from pyscf.lib import param


class KnownValues(unittest.TestCase):
    def test_scanner1(self):
        mol = neo.M(atom='H 0 0 0; F 0 0 0.94')
        mf = neo.CDFT(mol)
        pes_scanner = mf.as_scanner()
        grad_scanner = mf.nuc_grad_method().as_scanner()

        mol2 = neo.M(atom='H 0 0 0; F 0 0 1.1')
        mf2 = neo.CDFT(mol2)
        e_tot2 = mf2.scf()
        grad2 = mf2.Gradients().grad()
        e_tot, grad = grad_scanner(mol2)
        self.assertAlmostEqual(e_tot, e_tot2, 6)
        self.assertTrue(abs(grad-grad2).max() < 1e-6)
        e_tot = pes_scanner(mol2)
        self.assertAlmostEqual(e_tot, e_tot2, 6)

        mol2 = neo.M(atom='H 0 0 0; F 0 0 1.2')
        mf2 = neo.CDFT(mol2)
        e_tot2 = mf2.scf()
        grad2 = mf2.Gradients().grad()
        e_tot, grad = grad_scanner(mol2)
        self.assertAlmostEqual(e_tot, e_tot2, 6)
        self.assertTrue(abs(grad-grad2).max() < 1e-6)
        e_tot = pes_scanner(mol2)
        self.assertAlmostEqual(e_tot, e_tot2, 6)

    def test_scanner2(self):
        mol = neo.M(atom='H 0 0 0; F 0 0 0.94', basis='def2svp',
                    nuc_basis='pb4f1', quantum_nuc=[0,1])
        mf = neo.CDFT(mol)
        mf.conv_tol = 1e-11
        mf.conv_tol_grad = 1e-7
        mf.mf_elec.xc = 'M062X'
        mf.mf_elec.grids.atom_grid = (99, 590)
        pes_scanner = mf.as_scanner()
        grad_scanner = mf.Gradients().set(grid_response=True).as_scanner()

        mol2 = neo.M(atom='H 0 0 0; F 0 0 1.1', basis='def2svp',
                     nuc_basis='pb4f1', quantum_nuc=[0,1])
        mf2 = neo.CDFT(mol2)
        mf2.conv_tol = 1e-11
        mf2.conv_tol_grad = 1e-7
        mf2.mf_elec.xc = 'M062X'
        mf2.mf_elec.grids.atom_grid = (99, 590)
        e_tot2 = mf2.scf()
        grad2 = mf2.Gradients().set(grid_response=True).grad()

        mol3 = mol.copy()
        mol3.set_geom_(numpy.array([[0,0,0],[0,0,1.1/param.BOHR]]), unit='bohr')
        e_tot, grad = grad_scanner(mol3)
        self.assertAlmostEqual(e_tot, e_tot2, 7)
        self.assertTrue(abs(grad-grad2).max() < 1e-7)

        e_tot = pes_scanner('H 0 0 0; F 0 0 1.1')
        self.assertAlmostEqual(e_tot, e_tot2, 7)

        e_tot = pes_scanner(numpy.array([[0,0,0],[0,0,1.1]]))
        self.assertAlmostEqual(e_tot, e_tot2, 7)


if __name__ == "__main__":
    print("Testing as_scanner for neo SCF and Gradients")
    unittest.main()
