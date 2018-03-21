#!/usr/bin/env python3
## Extract chains' and polypeptides' sequences from PDB or mmCIF files. 
##
## Amaury Pupo Merino
## amaury.pupo@gmail.com
##
## This script is released under GPL v3.
##

## Importing modules
import argparse
import sys
from Bio.PDB import *
from Bio.PDB.Polypeptide import PPBuilder
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio import SeqIO
import os

## Functions
def get_info_from_header(structure):
    """Get info from a PDB's header.

    Try to get protein's name, source organism and resolution.
    """
    name=""
    organism=""
    resolution=-1.0

    name = structure.header.get('name')
    resolution = structure.header.get('resolution')

    if 'organism_scientific' in structure.header:
        organism = structure.header['organism_scientific']

    elif 'source' in structure.header:
        if type(structure.header['source']) == dict:
            if 'organism_scientific' in structure.header['source'].get('1'):
                organism = structure.header['source']['1']['organism_scientific']

    return (name, organism, resolution)

def get_info_from_cif_dict(filename):
    """Get info from CIF file.

    Try to get protein's name, source organism and resolution.
    """
    name=""
    organism=""
    resolution=-1.0
    cif_dict = MMCIF2Dict.MMCIF2Dict(filename)

    name = cif_dict.get("_entity_name_com.name")
    organism = cif_dict.get("_pdbx_entity_src_syn.organism_scientific")
    try:
        resolution = float(cif_dict.get("_reflns.d_resolution_high"))

    except:
        pass

    return (name, organism, resolution)

def write_seqs(filename):
    """Process a given structure file to extract sequences and save them into files.
    """
    struct_name = os.path.splitext(os.path.basename(filename))[0]
    is_CIF = False
    try:
        parser = PDBParser()
        structure = parser.get_structure(struct_name, filename)

    except:
        try:
            parser = MMCIFParser()
            structure = parser.get_structure(struct_name, filename)
            is_CIF = True

        except:
            sys.stderr.write("ERROR: File {} is not a proper/supported protein structure file.\n".format(filename))
            return

    if is_CIF:
        name, organism, resolution = get_info_from_cif_dict(filename)

    else:
        name, organism, resolution = get_info_from_header(structure)

    description = "| {} | {} | Resolution {:.2f} A".format(name, organism, resolution)

    ppb = PPBuilder()
    
    chain_seqrecord_list = []
    peptide_seqrecord_list = []
    for model in structure:
        for chain in model:
            base_id = "{}.{:d}_{}".format(struct_name, model.id, chain.id)
            chain_seq = Seq("")
            for (pp_id, pp) in enumerate(ppb.build_peptides(chain)):
                chain_seq += pp.get_sequence()
                peptide_seqrecord_list.append(SeqRecord(pp.get_sequence(), 
                    id = "{}.{:d}".format(base_id, pp_id),
                    description = description))

            chain_seqrecord_list.append(SeqRecord(chain_seq,
                id = base_id,
                description = description))

    base_output_name = os.path.splitext(filename)[0]
    
    SeqIO.write(chain_seqrecord_list, "{}_chains.fasta".format(base_output_name), "fasta")
    SeqIO.write(peptide_seqrecord_list, "{}_peptides.fasta".format(base_output_name), "fasta")

## Main
def main():
    """Main function.
    """
    parser=argparse.ArgumentParser(description="Extract chains' and polypeptides' sequences from PDB or mmCIF files.\nOnly the residues with structural information are saved. Residues missing in the structure give place to the possible existence of more than one polypeptide in each chain.\nTwo file are generated by input structure, one with each individual polypeptide sequence, and other with whole chain sequences, where peptides sequences within the chain are concatenated.\nOutput files are in fasta format, with an ID composed by <base_input_filename>.<Model_id>_<Chain_id> for chain sequences and <base_input_filename>.<Model_id>_<Chain_id>.<Peptide_id> for peptides.\nThe chain sequences files are particularly useful when you need to align target sequences against structural templates for molecular similarity modeling (the reason why I wrote this program in the first place).")
    parser.add_argument('structfile', nargs='+', help='Structure file (PDB or mmCIF).')
    parser.add_argument('-v', '--version', action='version', version='0.9.0', help="Show program's version number and exit.")

    args=parser.parse_args()

    for filename in args.structfile:
        write_seqs(filename)

## Running the script
if __name__ == "__main__":
    main()

