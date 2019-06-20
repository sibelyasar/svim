class Candidate:
    """Candidate class for structural variant candidates. Candidates reflect the final SV types and can be merged from signatures of several reads.
    """
    def __init__(self, source_contig, source_start, source_end, members, score, std_span, std_pos, support_fraction = ".", genotype = "./.", ref_reads = None, alt_reads = None):
        self.source_contig = source_contig
        self.source_start = source_start
        self.source_end = source_end
        
        self.members = members
        self.score = score
        self.std_span = std_span
        self.std_pos = std_pos
        self.type = None
        self.support_fraction = support_fraction
        self.genotype = genotype
        self.ref_reads = ref_reads
        self.alt_reads = alt_reads


    def get_source(self):
        return (self.source_contig, self.source_start, self.source_end)


    def get_key(self):
        contig, start, end = self.get_source()
        return (self.type, contig, (start + end) // 2)


    def position_distance_to(self, candidate2):
        """Return position distance between two candidates."""
        this_contig, this_start, this_end = self.get_source()
        other_contig, other_start, other_end = candidate2.get_source()
        this_center = (this_start + this_end) // 2
        other_center = (other_start + other_end) // 2
        if self.type == candidate2.type and this_contig == other_contig:
            return min(abs(this_start - other_start), abs(this_end - other_end), abs(this_center - other_center))
        else:
            return float("inf")


    def get_std_span(self, ndigits=2):
        if self.std_span:
            return round(self.std_span, ndigits)
        else:
            return "."


    def get_std_pos(self, ndigits=2):
        if self.std_pos:
            return round(self.std_pos, ndigits)
        else:
            return "."

    def get_bed_entry(self):
        return "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(self.source_contig, self.source_start, self.source_end, "{0};{1};{2}".format(self.type, self.get_std_span(), self.get_std_pos()), self.score, ".", "["+"][".join([ev.as_string("|") for ev in self.members])+"]")


    def get_vcf_entry(self):
        raise NotImplementedError


class CandidateDeletion(Candidate):
    def __init__(self, source_contig, source_start, source_end, members, score, std_span, std_pos, support_fraction = ".", genotype = "./.", ref_reads = None, alt_reads = None):
        self.source_contig = source_contig
        #0-based start of the deletion (first deleted base)
        self.source_start = source_start
        #0-based end of the deletion (one past the last deleted base)
        self.source_end = source_end

        self.members = members
        self.score = score
        self.std_span = std_span
        self.std_pos = std_pos
        self.type = "DEL"
        self.support_fraction = support_fraction
        self.genotype = genotype
        self.ref_reads = ref_reads
        self.alt_reads = alt_reads


    def get_vcf_entry(self):
        contig, start, end = self.get_source()
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=contig,
                    pos=start,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt="<" + self.type + ">",
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};END={1};SVLEN={2};SUPPORT={3};STD_SPAN={4};STD_POS={5}".format(self.type, end, start - end, len(set([sig.read for sig in self.members])), self.get_std_span(), self.get_std_pos()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))


class CandidateInversion(Candidate):
    def __init__(self, source_contig, source_start, source_end, members, score, std_span, std_pos, support_fraction = ".", genotype = "./.", ref_reads = None, alt_reads = None):
        self.source_contig = source_contig
        #0-based start of the inversion (first inverted base)
        self.source_start = source_start
        #0-based end of the inversion (one past the last inverted base)
        self.source_end = source_end

        self.members = members
        self.score = score
        self.std_span = std_span
        self.std_pos = std_pos
        self.type = "INV"
        self.support_fraction = support_fraction
        self.genotype = genotype
        self.ref_reads = ref_reads
        self.alt_reads = alt_reads


    def get_vcf_entry(self):
        contig, start, end = self.get_source()
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=contig,
                    pos=start+1,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt="<" + self.type + ">",
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};END={1};SUPPORT={2};STD_SPAN={3};STD_POS={4}".format(self.type, end, len(set([sig.read for sig in self.members])), self.get_std_span(), self.get_std_pos()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))


class CandidateNovelInsertion(Candidate):
    def __init__(self, dest_contig, dest_start, dest_end, members, score, std_span, std_pos, support_fraction = ".", genotype = "./.", ref_reads = None, alt_reads = None):
        self.dest_contig = dest_contig
        #0-based start of the insertion (base after the insertion)
        self.dest_start = dest_start
        #0-based start of the insertion (base after the insertion) + length of the insertion
        self.dest_end = dest_end

        self.members = members
        self.score = score
        self.std_span = std_span
        self.std_pos = std_pos
        self.type = "INS"
        self.support_fraction = support_fraction
        self.genotype = genotype
        self.ref_reads = ref_reads
        self.alt_reads = alt_reads

    def get_destination(self):
        return (self.dest_contig, self.dest_start, self.dest_end)

    def get_bed_entry(self):
        return "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}".format(self.dest_contig, self.dest_start, self.dest_end, "{0};{1};{2}".format(self.type, self.get_std_span(), self.get_std_pos()), self.score, ".", "["+"][".join([ev.as_string("|") for ev in self.members])+"]")

    def get_vcf_entry(self):
        contig, start, end = self.get_destination()
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=contig,
                    pos=start,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt="<" + self.type + ">",
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};END={1};SVLEN={2};SUPPORT={3};STD_SPAN={4};STD_POS={5}".format(self.type, start, end - start, len(set([sig.read for sig in self.members])), self.get_std_span(), self.get_std_pos()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))


class CandidateDuplicationTandem(Candidate):
    def __init__(self, source_contig, source_start, source_end, copies, fully_covered, members, score, std_span, std_pos, support_fraction = ".", genotype = "./.", ref_reads = None, alt_reads = None):
        self.source_contig = source_contig
        #0-based start of the region (first copied base)
        self.source_start = source_start
        #0-based end of the region (one past the last copied base)
        self.source_end = source_end
        
        self.copies = copies

        self.members = members
        self.score = score
        self.std_span = std_span
        self.std_pos = std_pos
        self.type = "DUP_TAN"
        self.support_fraction = support_fraction
        self.genotype = genotype
        self.ref_reads = ref_reads
        self.alt_reads = alt_reads
        self.fully_covered = fully_covered


    def get_destination(self):
        source_contig, source_start, source_end = self.get_source()
        return (source_contig, source_end, source_end + self.copies * (source_end - source_start))


    def get_bed_entries(self, sep="\t"):
        source_contig, source_start, source_end = self.get_source()
        dest_contig, dest_start, dest_end = self.get_destination()
        source_entry = sep.join(["{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}"]).format(source_contig, source_start,
                                                                                     source_end,
                                                                                     "tan_dup_source;>{0}:{1}-{2};{3};{4}".format(
                                                                                         dest_contig, dest_start,
                                                                                         dest_end, self.get_std_span(), self.get_std_pos()), self.score, ".",
                                                                                     "[" + "][".join(
                                                                                         [ev.as_string("|") for ev in
                                                                                          self.members]) + "]")
        dest_entry = sep.join(["{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}"]).format(dest_contig, dest_start, dest_end,
                                                                                   "tan_dup_dest;<{0}:{1}-{2};{3};{4}".format(
                                                                                       source_contig, source_start,
                                                                                       source_end, self.get_std_span(), self.get_std_pos()), self.score, ".",
                                                                                   "[" + "][".join(
                                                                                       [ev.as_string("|") for ev in
                                                                                        self.members]) + "]")
        return (source_entry, dest_entry)


    def get_vcf_entry_as_ins(self):
        contig = self.source_contig
        start = self.source_end
        end = self.source_end + self.copies * (self.source_end - self.source_start)
        svtype = "INS"
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        if not(self.fully_covered):
            filters.append("not_fully_covered")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=contig,
                    pos=start,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt="<" + svtype + ">",
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};END={1};SVLEN={2};SUPPORT={3};STD_SPAN={4};STD_POS={5}".format(svtype, start, end - start, len(set([sig.read for sig in self.members])), self.get_std_span(), self.get_std_pos()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))


    def get_vcf_entry_as_dup(self):
        contig = self.source_contig
        start = self.source_start
        end = self.source_end
        length = self.copies * (self.source_end - self.source_start)
        svtype = "DUP:TANDEM"
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        if not(self.fully_covered):
            filters.append("not_fully_covered")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=contig,
                    pos=start,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt="<" + svtype + ">",
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};END={1};SVLEN={2};SUPPORT={3};STD_SPAN={4};STD_POS={5}".format(svtype, end, length, len(set([sig.read for sig in self.members])), self.get_std_span(), self.get_std_pos()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))


class CandidateDuplicationInterspersed(Candidate):
    def __init__(self, source_contig, source_start, source_end, dest_contig, dest_start, dest_end, members, score, std_span, std_pos, cutpaste=False, support_fraction = ".", genotype = "./.", ref_reads = None, alt_reads = None):
        self.source_contig = source_contig
        #0-based start of the region (first copied base)
        self.source_start = source_start
        #0-based end of the region (one past the last copied base)
        self.source_end = source_end

        self.dest_contig = dest_contig
        #0-based start of the insertion (base after the insertion)
        self.dest_start = dest_start
        #0-based end of the insertion (base after the insertion) + length of the insertion
        self.dest_end = dest_end

        self.members = members
        self.score = score
        self.std_span = std_span
        self.std_pos = std_pos
        self.cutpaste= cutpaste
        self.type = "DUP_INT"
        self.support_fraction = support_fraction
        self.genotype = genotype
        self.ref_reads = ref_reads
        self.alt_reads = alt_reads


    def get_destination(self):
        return (self.dest_contig, self.dest_start, self.dest_end)


    def get_bed_entries(self, sep="\t"):
        source_contig, source_start, source_end = self.get_source()
        dest_contig, dest_start, dest_end = self.get_destination()
        source_entry = sep.join(["{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}"]).format(source_contig, source_start,
                                                                                     source_end,
                                                                                     "int_dup_source;>{0}:{1}-{2};{3};{4}".format(
                                                                                         dest_contig, dest_start,
                                                                                         dest_end, self.get_std_span(), self.get_std_pos()), self.score, "origin potentially deleted" if self.cutpaste else ".",
                                                                                     "[" + "][".join(
                                                                                         [ev.as_string("|") for ev in
                                                                                          self.members]) + "]")
        dest_entry = sep.join(["{0}", "{1}", "{2}", "{3}", "{4}", "{5}", "{6}"]).format(dest_contig, dest_start, dest_end,
                                                                                   "int_dup_dest;<{0}:{1}-{2};{3};{4}".format(
                                                                                       source_contig, source_start,
                                                                                       source_end, self.get_std_span(), self.get_std_pos()), self.score, "origin potentially deleted" if self.cutpaste else ".",
                                                                                   "[" + "][".join(
                                                                                       [ev.as_string("|") for ev in
                                                                                        self.members]) + "]")
        return (source_entry, dest_entry)


    def get_vcf_entry_as_ins(self):
        contig, start, end = self.get_destination()
        svtype = "INS"
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=contig,
                    pos=start,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt="<" + svtype + ">",
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};{1}END={2};SVLEN={3};SUPPORT={4};STD_SPAN={5};STD_POS={6}".format(svtype, "CUTPASTE;" if self.cutpaste else "", start, end - start, len(set([sig.read for sig in self.members])), self.get_std_span(), self.get_std_pos()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))


    def get_vcf_entry_as_dup(self):
        contig, start, end = self.get_source()
        svtype = "DUP_INT"
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=contig,
                    pos=start,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt="<" + svtype + ">",
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};{1}END={2};SVLEN={3};SUPPORT={4};STD_SPAN={5};STD_POS={6}".format(svtype, "CUTPASTE;" if self.cutpaste else "", end, end - start, len(set([sig.read for sig in self.members])), self.get_std_span(), self.get_std_pos()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))


class CandidateBreakend(Candidate):
    def __init__(self, source_contig, source_start, source_direction, dest_contig, dest_start, dest_direction, members, score, std_pos1, std_pos2, support_fraction = ".", genotype = "./.", ref_reads = None, alt_reads = None):
        self.source_contig = source_contig
        #0-based source of the translocation (first base before the translocation)
        self.source_start = source_start
        self.source_direction = source_direction

        self.dest_contig = dest_contig
        #0-based destination of the translocation (first base after the translocation)
        self.dest_start = dest_start
        self.dest_direction = dest_direction

        self.members = members
        self.score = score
        self.std_pos1 = std_pos1
        self.std_pos2 = std_pos2
        self.type = "BND"
        self.support_fraction = support_fraction
        self.genotype = genotype
        self.ref_reads = ref_reads
        self.alt_reads = alt_reads


    def get_source(self):
        return (self.source_contig, self.source_start)


    def get_destination(self):
        return (self.dest_contig, self.dest_start)


    def get_std_pos1(self, ndigits=2):
        if self.std_pos1:
            return round(self.std_pos1, ndigits)
        else:
            return "."


    def get_std_pos2(self, ndigits=2):
        if self.std_pos2:
            return round(self.std_pos2, ndigits)
        else:
            return "."


    def get_bed_entries(self, sep="\t"):
        source_contig, source_start = self.get_source()
        dest_contig, dest_start = self.get_destination()
        source_entry = sep.join(["{0}", "{1}", "{2}", "{3}", "{4}", "{5}"]).format(source_contig, 
                                                                                   source_start,
                                                                                   source_start + 1,
                                                                                   "bnd;>{0}:{1};{2};{3}".format(
                                                                                        dest_contig, dest_start, self.get_std_pos1(), self.get_std_pos2()), 
                                                                                   self.score, 
                                                                                   "[" + "][".join(
                                                                                        [ev.as_string("|") for ev in self.members]) + "]")
        dest_entry = sep.join(["{0}", "{1}", "{2}", "{3}", "{4}", "{5}"]).format(dest_contig, 
                                                                                 dest_start, 
                                                                                 dest_start + 1,
                                                                                 "bnd;<{0}:{1};{2};{3}".format(
                                                                                        source_contig, source_start, self.get_std_pos1(), self.get_std_pos2()), 
                                                                                 self.score,
                                                                                 "[" + "][".join(
                                                                                        [ev.as_string("|") for ev in self.members]) + "]")
        return (source_entry, dest_entry)


    def get_vcf_entry(self):
        source_contig, source_start = self.get_source()
        dest_contig, dest_start = self.get_destination()
        if (self.source_direction == 'fwd') and (self.dest_direction == 'fwd'):
            alt_string = "N[{contig}:{start}[".format(contig = dest_contig, start = dest_start)
        elif (self.source_direction == 'fwd') and (self.dest_direction == 'rev'):
            alt_string = "N]{contig}:{start}]".format(contig = dest_contig, start = dest_start)
        elif (self.source_direction == 'rev') and (self.dest_direction == 'rev'):
            alt_string = "]{contig}:{start}]N".format(contig = dest_contig, start = dest_start)
        elif (self.source_direction == 'rev') and (self.dest_direction == 'fwd'):
            alt_string = "[{contig}:{start}[N".format(contig = dest_contig, start = dest_start)
        if self.ref_reads != None and self.alt_reads != None:
            dp_string = str(self.ref_reads + self.alt_reads)
        else:
            dp_string = "."
        filters = []
        if self.score < 5:
            filters.append("q5")
        if self.genotype == 0:
            filters.append("hom_ref")
        return "{chrom}\t{pos}\t{id}\t{ref}\t{alt}\t{qual}\t{filter}\t{info}\t{format}\t{samples}".format(
                    chrom=source_contig,
                    pos=source_start,
                    id="PLACEHOLDERFORID",
                    ref="N",
                    alt=alt_string,
                    qual=int(self.score),
                    filter="PASS" if len(filters) == 0 else ";".join(filters),
                    info="SVTYPE={0};SUPPORT={1};STD_POS1={2};STD_POS2={3}".format(self.type, len(set([sig.read for sig in self.members])), self.get_std_pos1(), self.get_std_pos2()),
                    format="GT:DP:AD",
                    samples="{gt}:{dp}:{ref},{alt}".format(gt=self.genotype, dp=dp_string, ref=self.ref_reads if self.ref_reads != None else ".", alt=self.alt_reads if self.alt_reads != None else "."))
