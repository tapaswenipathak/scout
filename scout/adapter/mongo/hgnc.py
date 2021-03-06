import logging
from pprint import pprint as pp
import intervaltree

from scout.build.genes.exon import build_exon
from pymongo.errors import (DuplicateKeyError, BulkWriteError)

from scout.exceptions import IntegrityError

LOG = logging.getLogger(__name__)

class GeneHandler(object):

    def load_hgnc_gene(self, gene_obj):
        """Add a gene object with transcripts to the database

        Arguments:
            gene_obj(dict)

        """
        #LOG.debug("Loading gene %s, build %s into database" %
        #             (gene_obj['hgnc_symbol'], gene_obj['build']))
        res = self.hgnc_collection.insert_one(gene_obj)
        #LOG.debug("Gene saved")
        return res

    def load_hgnc_bulk(self, gene_objs):
        """Load a bulk of hgnc gene objects

        Raises IntegrityError if there are any write concerns

        Args:
            gene_objs(iterable(scout.models.hgnc_gene))

        Returns:
            result (pymongo.results.InsertManyResult)
        """

        LOG.info("Loading gene bulk with length %s", len(gene_objs))
        try:
            result = self.hgnc_collection.insert_many(gene_objs)
        except (DuplicateKeyError, BulkWriteError) as err:
            raise IntegrityError(err)

        return result

    def load_hgnc_transcript(self, transcript_obj):
        """Add a transcript object to the database

        Arguments:
            transcript_obj(dict)

        """
        res = self.transcript_collection.insert_one(transcript_obj)
        return res

    def load_transcript_bulk(self, transcript_objs):
        """Load a bulk of transcript objects to the database

        Arguments:
            transcript_objs(iterable(scout.models.hgnc_transcript))

        """
        LOG.info("Loading transcript bulk")
        try:
            result = self.transcript_collection.insert_many(transcript_objs)
        except (DuplicateKeyError, BulkWriteError) as err:
            raise IntegrityError(err)

        return result

    def load_exon(self, exon_obj):
        """Add a exon object to the database

        Arguments:
            exon_obj(dict)

        """
        res = self.exon_collection.insert_one(exon_obj)
        return res

    def load_exon_bulk(self, exon_objs):
        """Load a bulk of exon objects to the database

        Arguments:
            exon_objs(iterable(scout.models.hgnc_exon))

        """
        try:
            result = self.exon_collection.insert_many(transcript_objs)
        except (DuplicateKeyError, BulkWriteError) as err:
            raise IntegrityError(err)

        return result

    def hgnc_gene(self, hgnc_identifier, build='37'):
        """Fetch a hgnc gene

            Args:
                hgnc_identifier(int)

            Returns:
                gene_obj(HgncGene)
        """
        if not build in ['37', '38']:
            build = '37'
        query = {}
        try:
            # If the identifier is a integer we search for hgnc_id
            hgnc_identifier = int(hgnc_identifier)
            query['hgnc_id'] = hgnc_identifier
        except ValueError:
            # Else we seach for a hgnc_symbol
            query['hgnc_symbol'] = hgnc_identifier

        query['build'] = build
        LOG.debug("Fetching gene %s" % hgnc_identifier)
        gene_obj = self.hgnc_collection.find_one(query)
        if not gene_obj:
            return None

        # Add the transcripts:
        transcripts = []
        tx_objs = self.transcripts(build=build, hgnc_id=gene_obj['hgnc_id'])
        if tx_objs.count() > 0:
            for tx in tx_objs:
                transcripts.append(tx)
        gene_obj['transcripts'] = transcripts

        return gene_obj

    def hgnc_id(self, hgnc_symbol, build='37'):
        """Query the genes with a hgnc symbol and return the hgnc id

        Args:
            hgnc_symbol(str)
            build(str)

        Returns:
            hgnc_id(int)
        """
        #LOG.debug("Fetching gene %s", hgnc_symbol)
        query = {'hgnc_symbol':hgnc_symbol, 'build':build}
        projection = {'hgnc_id':1, '_id':0}
        res = self.hgnc_collection.find(query, projection)

        if res.count() > 0:
            return res[0]['hgnc_id']
        else:
            return None

    def hgnc_genes(self, hgnc_symbol, build='37', search=False):
        """Fetch all hgnc genes that match a hgnc symbol

            Check both hgnc_symbol and aliases

            Args:
                hgnc_symbol(str)
                build(str): The build in which to search
                search(bool): if partial searching should be used

            Returns:
                result()
        """
        LOG.debug("Fetching genes with symbol %s" % hgnc_symbol)
        if search:
            # first search for a full match
            full_query = self.hgnc_collection.find({
                '$or': [
                    {'aliases': hgnc_symbol},
                    {'hgnc_id': int(hgnc_symbol) if hgnc_symbol.isdigit() else None},
                ],
                'build': build
            })
            if full_query.count() != 0:
                return full_query

            return self.hgnc_collection.find({
                'aliases': {'$regex': hgnc_symbol, '$options': 'i'},
                'build': build
            })

        return self.hgnc_collection.find({'build': build, 'aliases': hgnc_symbol})

    def all_genes(self, build='37'):
        """Fetch all hgnc genes

            Returns:
                result()
        """
        LOG.info("Fetching all genes")
        return self.hgnc_collection.find({'build': build}).sort('chromosome', 1)

    def nr_genes(self, build=None):
        """Return the number of hgnc genes in collection

        If build is used, return the number of genes of a certain build

            Returns:
                result()
        """
        if build:
            LOG.info("Fetching all genes from build %s",  build)
        else:
            LOG.info("Fetching all genes")

        return self.hgnc_collection.find({'build':build}).count()

    def drop_genes(self, build=None):
        """Delete the genes collection"""
        if build:
            LOG.info("Dropping the hgnc_gene collection, build %s", build)
            self.hgnc_collection.delete_many({'build': build})
        else:
            LOG.info("Dropping the hgnc_gene collection")
            self.hgnc_collection.drop()

    def drop_transcripts(self, build=None):
        """Delete the transcripts collection"""
        if build:
            LOG.info("Dropping the transcripts collection, build %s", build)
            self.transcript_collection.delete_many({'build': build})
        else:
            LOG.info("Dropping the transcripts collection")
            self.transcript_collection.drop()

    def drop_exons(self, build=None):
        """Delete the exons collection"""
        if build:
            LOG.info("Dropping the exons collection, build %s", build)
            self.exon_collection.delete_many({'build': build})
        else:
            LOG.info("Dropping the exons collection")
            self.exon_collection.drop()

    def ensembl_transcripts(self, build='37'):
        """Return a dictionary with ensembl ids as keys and transcripts as value.

        Args:
            build(str)

        Returns:
            ensembl_transcripts(dict): {<enst_id>: transcripts_obj, ...}
        """
        ensembl_transcripts = {}
        LOG.info("Fetching all transcripts")
        for transcript_obj in self.transcript_collection.find({'build':build}):
            enst_id = transcript_obj['transcript_id']
            ensembl_transcripts[enst_id] = transcript_obj
        LOG.info("Ensembl transcripts fetched")

        return ensembl_transcripts

    def hgncid_to_gene(self, build='37', genes=None):
        """Return a dictionary with hgnc_id as key and gene_obj as value

        The result will have ONE entry for each gene in the database.
        (For a specific build)

        Args:
            build(str):
            genes(iterable(scout.models.HgncGene)):

        Returns:
            hgnc_dict(dict): {<hgnc_id(int)>: <gene(dict)>}

        """
        hgnc_dict = {}
        LOG.info("Building hgncid_to_gene")
        if not genes:
            genes = self.hgnc_collection.find({'build':build})

        for gene_obj in genes:
            hgnc_dict[gene_obj['hgnc_id']] = gene_obj

        return hgnc_dict

    def hgncsymbol_to_gene(self, build='37', genes=None):
        """Return a dictionary with hgnc_symbol as key and gene_obj as value

        The result will have ONE entry for each gene in the database.
        (For a specific build)

        Args:
            build(str)
            genes(iterable(scout.models.HgncGene)):

        Returns:
            hgnc_dict(dict): {<hgnc_symbol(str)>: <gene(dict)>}

        """
        hgnc_dict = {}
        LOG.info("Building hgncsymbol_to_gene")
        if not genes:
            genes = self.hgnc_collection.find({'build':build})

        for gene_obj in genes:
            hgnc_dict[gene_obj['hgnc_symbol']] = gene_obj
        LOG.info("All genes fetched")
        return hgnc_dict

    def gene_by_alias(self, symbol, build='37'):
        """Return a iterable with hgnc_genes.

        If the gene symbol is listed as primary the iterable will only have
        one result. If not the iterable will include all hgnc genes that have
        the symbol as an alias.

        Args:
            symbol(str)
            build(str)

        Returns:
            res(pymongo.Cursor(dict))
        """
        res = self.hgnc_collection.find({'hgnc_symbol': symbol, 'build':build})
        if res.count() == 0:
            res = self.hgnc_collection.find({'aliases': symbol, 'build':build})

        return res

    def genes_by_alias(self, build='37', genes=None):
        """Return a dictionary with hgnc symbols as keys and a list of hgnc ids
             as value.

        If a gene symbol is listed as primary the list of ids will only consist
        of that entry if not the gene can not be determined so the result is a list
        of hgnc_ids

        Args:
            build(str)
            genes(iterable(scout.models.HgncGene)):

        Returns:
            alias_genes(dict): {<hgnc_alias>: {'true': <hgnc_id>, 'ids': {<hgnc_id_1>, <hgnc_id_2>, ...}}}
        """
        LOG.info("Fetching all genes by alias")
        # Collect one entry for each alias symbol that exists
        alias_genes = {}
        # Loop over all genes
        if not genes:
            genes = self.hgnc_collection.find({'build':build})

        for gene in genes:
            # Collect the hgnc_id
            hgnc_id = gene['hgnc_id']
            # Collect the true symbol given by hgnc
            hgnc_symbol = gene['hgnc_symbol']
            # Loop aver all aliases
            for alias in gene['aliases']:
                true_id = None
                # If the alias is the same as hgnc symbol we know the true id
                if alias == hgnc_symbol:
                    true_id = hgnc_id
                # If the alias is already in the list we add the id
                if alias in alias_genes:
                    alias_genes[alias]['ids'].add(hgnc_id)
                    if true_id:
                        alias_genes[alias]['true'] = hgnc_id
                else:
                    alias_genes[alias] = {
                        'true': hgnc_id,
                        'ids': set([hgnc_id])
                    }

        return alias_genes

    def get_id_transcripts(self, hgnc_id, build='37'):
        """Return a set with identifier transcript(s)

        Choose all refseq transcripts with NM symbols, if none where found choose ONE with NR,
        if no NR choose ONE with XM. If there are no RefSeq transcripts identifiers choose the
        longest ensembl transcript.

        Args:
            hgnc_id(int)
            build(str)

        Returns:
            identifier_transcripts(set)

        """
        transcripts = self.transcripts(build=build, hgnc_id=hgnc_id)

        identifier_transcripts = set()
        longest = None
        nr = []
        xm = []
        for tx in transcripts:
            enst_id = tx['transcript_id']
            # Should we not check if it is longest?
            if not longest:
                longest = enst_id
            refseq_id = tx.get('refseq_id')
            if not refseq_id:
                continue

            if 'NM' in refseq_id:
                identifier_transcripts.add(enst_id)
            elif 'NR' in refseq_id:
                nr.append(enst_id)
            elif 'XM' in refseq_id:
                xm.append(enst_id)

        if identifier_transcripts:
            return identifier_transcripts

        if nr:
            return set([nr[0]])

        if xm:
            return set([xm[0]])

        return set([longest])

    def transcripts_by_gene(self, build='37'):
        """Return a dictionary with hgnc_id as keys and a list of transcripts as value

        Args:
            build(str)

        Returns:
            hgnc_transcripts(dict)

        """
        hgnc_transcripts = {}
        LOG.info("Fetching all transcripts")
        for transcript in self.transcript_collection.find({'build':build}):
            hgnc_id = transcript['hgnc_id']
            if not hgnc_id in hgnc_transcripts:
                hgnc_transcripts[hgnc_id] = []

            hgnc_transcripts[hgnc_id].append(transcript)

        return hgnc_transcripts

    def id_transcripts_by_gene(self, build='37'):
        """Return a dictionary with hgnc_id as keys and a set of id transcripts as value

        Args:
            build(str)

        Returns:
            hgnc_id_transcripts(dict)
        """
        hgnc_id_transcripts = {}
        LOG.info("Fetching all id transcripts")
        for gene_obj in self.hgnc_collection.find({'build': build}):
            hgnc_id = gene_obj['hgnc_id']
            id_transcripts = self.get_id_transcripts(hgnc_id=hgnc_id, build=build)
            hgnc_id_transcripts[hgnc_id] = id_transcripts

        return hgnc_id_transcripts

    def ensembl_genes(self, build='37'):
        """Return a dictionary with ensembl ids as keys and gene objects as value.

        Args:
            build(str)

        Returns:
            genes(dict): {<ensg_id>: gene_obj, ...}
        """
        genes = {}

        LOG.info("Fetching all genes")
        for gene_obj in self.hgnc_collection.find({'build':build}):
            ensg_id = gene_obj['ensembl_id']
            hgnc_id = gene_obj['hgnc_id']

            genes[ensg_id] = gene_obj

        LOG.info("Ensembl genes fetched")

        return genes

    def transcripts(self, build='37', hgnc_id=None):
        """Return all transcripts.

            If a gene is specified return all transcripts for the gene

        Args:
            build(str)
            hgnc_id(int)

        Returns:
            iterable(transcript)
        """

        query = {'build': build}
        if hgnc_id:
            query['hgnc_id'] = hgnc_id

        return self.transcript_collection.find(query)


    def to_hgnc(self, hgnc_alias, build='37'):
        """Check if a hgnc symbol is an alias

            Return the correct hgnc symbol, if not existing return None

            Args:
                hgnc_alias(str)

            Returns:
                hgnc_symbol(str)
        """
        result = self.hgnc_genes(hgnc_symbol=hgnc_alias, build=build)
        if result:
            for gene in result:
                return gene['hgnc_symbol']
        else:
            return None

    def add_hgnc_id(self, genes):
        """Add the correct hgnc id to a set of genes with hgnc symbols

        Args:
            genes(list(dict)): A set of genes with hgnc symbols only

        """
        genes_by_alias = self.genes_by_alias()

        for gene in genes:
            id_info = genes_by_alias.get(gene['hgnc_symbol'])
            if not id_info:
                LOG.warning("Gene %s does not exist in scout", gene['hgnc_symbol'])
                continue
            gene['hgnc_id'] = id_info['true']
            if not id_info['true']:
                if len(id_info['ids']) > 1:
                    LOG.warning("Gene %s has ambiguous value, please choose one hgnc id in result", gene['hgnc_symbol'])
                gene['hgnc_id'] = ','.join([str(hgnc_id) for hgnc_id in id_info['ids']])

    def get_coding_intervals(self, build='37', genes=None):
        """Return a dictionary with chromosomes as keys and interval trees as values

        Each interval represents a coding region of overlapping genes.

        Args:
            build(str): The genome build
            genes(iterable(scout.models.HgncGene)):

        Returns:
            intervals(dict): A dictionary with chromosomes as keys and overlapping genomic intervals as values
        """
        intervals = {}
        if not genes:
            genes = self.all_genes(build=build)
        LOG.info("Building interval trees...")
        for i,hgnc_obj in enumerate(genes):
            chrom = hgnc_obj['chromosome']
            start = max((hgnc_obj['start'] - 5000), 1)
            end = hgnc_obj['end'] + 5000

            # If this is the first time a chromosome is seen we create a new
            # interval tree with current interval
            if chrom not in intervals:
                intervals[chrom] = intervaltree.IntervalTree()
                intervals[chrom].addi(start, end, i)
                continue

            res = intervals[chrom].search(start, end)

            # If the interval did not overlap any other intervals we insert it and continue
            if not res:
                intervals[chrom].addi(start, end, i)
                continue

            # Loop over the overlapping intervals
            for interval in res:
                # Update the positions to new max and mins
                if interval.begin < start:
                    start = interval.begin

                if interval.end > end:
                    end = interval.end

                # Delete the old interval
                intervals[chrom].remove(interval)

            # Add the new interval consisting och the overlapping ones
            intervals[chrom].addi(start, end, i)

        return intervals

    def load_exons(self, exons, genes=None, build='37'):
        """Create exon objects and insert them into the database

        Args:
            exons(iterable(dict))
        """
        genes = genes or self.ensembl_genes(build)
        for exon in exons:
            exon_obj = build_exon(exon, genes)
            if not exon_obj:
                continue

            res = self.exon_collection.insert_one(exon_obj)

    def exons(self, hgnc_id=None, transcript_id=None,  build=None):
        """Return all exons

        Args:
            hgnc_id(int)
            transcript_id(str)
            build(str)

        Returns:
            exons(iterable(dict))
        """
        query = {}
        if build:
            query['build'] = build
        if hgnc_id:
            query['hgnc_id'] = hgnc_id
        if transcript_id:
            query['transcript_id'] = transcript_id

        return self.exon_collection.find(query)
