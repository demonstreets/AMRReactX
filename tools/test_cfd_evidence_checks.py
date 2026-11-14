#!/usr/bin/env python3
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import cfd_evidence_checks as checks
import cfd_run_archive as archive
from test_amrex_reader_multibox import write_plotfile


class EvidenceChecks(unittest.TestCase):
    def test_run_scoped_log_checks(self):
        from check_cfd_run_log import check_log
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'run.log'
            p.write_text('CVODE reactor initialized; information follows\nAMReX (test) finalized\n')
            self.assertIn('PASS',check_log(p,0))
            with self.assertRaises(ValueError):check_log(p,6)
            p.write_text('CVODE solve failed, flag=-4\nAMReX (test) finalized\n')
            with self.assertRaises(ValueError):check_log(p,0)
            p.write_text('amrex::Abort::Simulation stopped early\n')
            with self.assertRaises(ValueError):check_log(p,0)


    def pair(self, reacts=True, cold=False):
        shape=(8,2,2)
        fields={'density':np.ones(shape), 'Temp':np.full(shape,300.)}
        if not cold: fields['Temp'][0]=1000.
        species=('H2','O2','H2O','H','O','OH','HO2','H2O2','N2')
        for name in species: fields['rho_'+name]=np.zeros(shape)
        fields['rho_H2'][:]=.1;fields['rho_O2'][:]=.8;fields['rho_H2O'][:]=.1
        initial={'fields':fields,'time':0.,'dx':[1.,1.,1.]}
        final=copy.deepcopy(initial);final['time']=1.
        if reacts:
            final['fields']['rho_H2']-=.01
            final['fields']['rho_O2']-=.08
            final['fields']['rho_H2O']+=.09
        return initial,final

    def test_pressure_front_and_cold_rejection(self):
        x=np.arange(10)+.5
        p=np.where(x<5,10.,1.)[:,None,None]
        self.assertEqual(checks.pressure_front_x(p,x),5.)
        with self.assertRaises(ValueError): checks.pressure_front_x(np.ones_like(p),x)

    def test_real_conversion_passes(self):
        with patch('amrex_reader.read_plotfile',side_effect=self.pair()):
            result=checks.reacting_pair_metrics('initial','final')
        self.assertAlmostEqual(result['fuel_consumed_fraction'],.1)
        self.assertFalse(result['detonation_propagation_verified'])

    def test_cold_runtime_rejected(self):
        with patch('amrex_reader.read_plotfile',side_effect=self.pair(cold=True)):
            with self.assertRaisesRegex(ValueError,'hotspot absent'):
                checks.reacting_pair_metrics('initial','final')

    def test_hot_but_nonreacting_rejected(self):
        with patch('amrex_reader.read_plotfile',side_effect=self.pair(reacts=False)):
            with self.assertRaisesRegex(ValueError,'no resolved chemical conversion'):
                checks.reacting_pair_metrics('initial','final')

    def test_negative_species_rejected(self):
        pair=self.pair();pair[1]['fields']['rho_O2'][3,0,0]=-7.e-5
        with patch('amrex_reader.read_plotfile',side_effect=pair):
            with self.assertRaisesRegex(ValueError,'unphysical mass fraction'):
                checks.reacting_pair_metrics('initial','final')

    def test_finite_and_closure_checks(self):
        for bad in (float('nan'),.9):
            pair=self.pair();pair[1]['fields']['rho_O2'][3,0,0]=bad
            with patch('amrex_reader.read_plotfile',side_effect=pair):
                with self.assertRaises(ValueError): checks.reacting_pair_metrics('initial','final')

    def test_archived_zero_chemistry_identified(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plot=root/'run/plt00000';plot.mkdir(parents=True)
            (plot/'job_info').write_text('CHEMISTRY: inert_test\n')
            mechanism=root/'external/PeleC/Submodules/PelePhysics/Mechanisms/inert_test/mechanism.H'
            mechanism.parent.mkdir(parents=True);mechanism.write_text('#define NUM_GAS_REACTIONS 0\n')
            with patch.object(checks,'__file__',str(root/'tools/cfd_evidence_checks.py')):
                result=checks.archived_chemistry(plot)
            self.assertEqual(result['gas_reactions'],0)
            self.assertFalse(result['binary_provenance_verified'])

    def test_archive_missing_payload_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);run=root/'run';plot=run/'plt00000'
            write_plotfile(plot,2,[(0,1,0,1,0,0)])
            executable=root/'solver.ex';executable.write_bytes(b'test executable identity')
            destination=root/'archive'
            archive.archive_run(run,destination,root,executable)
            archive.verify_archive(destination)
            with self.assertRaises(ValueError): archive.archive_run(run,destination,root,executable)
            # A manifest checksum detects mutation even if the file still exists.
            (destination/'run/plt00000/Level_0/Cell_D_00000').write_bytes(b'broken')
            with self.assertRaises(ValueError): archive.verify_archive(destination)
            (plot/'Level_0/Cell_D_00000').unlink()
            with self.assertRaises(ValueError): archive.check_plotfile(plot)

    def test_source_drift_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'src').mkdir();source=root/'src/model.cpp';source.write_text('version one')
            manifest=archive.source_fingerprint(root,['src'])
            import json
            m=root/'sources.json';m.write_text(json.dumps(manifest))
            run=root/'run';write_plotfile(run/'plt00000',2,[(0,1,0,1,0,0)])
            executable=root/'solver.ex';executable.write_bytes(b'binary')
            source.write_text('version two')
            with self.assertRaisesRegex(ValueError,'source changed'):
                archive.archive_run(run,root/'archive',root,executable,m)


if __name__ == '__main__':
    unittest.main()
