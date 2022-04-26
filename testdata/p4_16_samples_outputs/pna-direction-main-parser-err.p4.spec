
struct ethernet_t {
	bit<48> dstAddr
	bit<48> srcAddr
	bit<16> etherType
}

struct ipv4_t {
	bit<8> version_ihl
	bit<8> diffserv
	bit<16> totalLen
	bit<16> identification
	bit<16> flags_fragOffset
	bit<8> ttl
	bit<8> protocol
	bit<16> hdrChecksum
	bit<32> srcAddr
	bit<32> dstAddr
}

struct next_hop_0_arg_t {
	bit<32> vport
}

struct main_metadata_t {
	bit<32> pna_pre_input_metadata_input_port
	bit<32> pna_pre_input_metadata_direction
	bit<32> pna_main_parser_input_metadata_direction
	bit<32> pna_main_parser_input_metadata_input_port
	bit<32> pna_main_input_metadata_input_port
	bit<32> local_metadata_tmpDir
	bit<32> pna_main_output_metadata_output_port
	bit<32> MainParserT_parser_tmp
	bit<32> reg_read_tmp
	bit<32> left_shift_tmp
}
metadata instanceof main_metadata_t

header ethernet instanceof ethernet_t
header ipv4 instanceof ipv4_t

regarray network_port_mask size 0x1 initval 0

action next_hop_0 args instanceof next_hop_0_arg_t {
	mov m.pna_main_output_metadata_output_port t.vport
	return
}

action default_route_drop_0 args none {
	drop
	return
}

table ipv4_da_lpm {
	key {
		m.local_metadata_tmpDir lpm
	}
	actions {
		next_hop_0
		default_route_drop_0
	}
	default_action default_route_drop_0 args none 
	size 0x10000
}


apply {
	rx m.pna_main_input_metadata_input_port
	extract h.ethernet
	jmpeq MAINPARSERIMPL_PARSE_IPV4 h.ethernet.etherType 0x800
	jmp MAINPARSERIMPL_ACCEPT
	MAINPARSERIMPL_PARSE_IPV4 :	extract h.ipv4
	jmpeq MAINPARSERIMPL_PARSE_IPV4_TRUE m.MainParserT_parser_tmp 0x1
	jmpeq MAINPARSERIMPL_PARSE_IPV4_FALSE m.MainParserT_parser_tmp 0x0
	jmp MAINPARSERIMPL_NOMATCH
	MAINPARSERIMPL_PARSE_IPV4_TRUE :	mov m.local_metadata_tmpDir h.ipv4.srcAddr
	jmp MAINPARSERIMPL_ACCEPT
	MAINPARSERIMPL_PARSE_IPV4_FALSE :	regrd m.reg_read_tmp network_port_mask 0x0
	mov m.left_shift_tmp 0x1
	shl m.left_shift_tmp m.pna_main_parser_input_metadata_input_port
	mov m.pna_main_parser_input_metadata_direction m.reg_read_tmp
	and m.pna_main_parser_input_metadata_direction m.left_shift_tmp
	jmpneq LABEL_FALSE 0x0 m.pna_main_parser_input_metadata_direction
	mov m.MainParserT_parser_tmp 0x1
	jmp LABEL_END
	LABEL_FALSE :	mov m.MainParserT_parser_tmp 0x0
	LABEL_END :	mov m.local_metadata_tmpDir h.ipv4.dstAddr
	jmp MAINPARSERIMPL_ACCEPT
	MAINPARSERIMPL_NOMATCH :	mov m.pna_pre_input_metadata_parser_error 0x2
	MAINPARSERIMPL_ACCEPT :	regrd m.reg_read_tmp network_port_mask 0x0
	mov m.left_shift_tmp 0x1
	shl m.left_shift_tmp m.pna_pre_input_metadata_input_port
	mov m.pna_pre_input_metadata_direction m.reg_read_tmp
	and m.pna_pre_input_metadata_direction m.left_shift_tmp
	jmpneq LABEL_FALSE_0 0x0 m.pna_pre_input_metadata_direction
	mov m.local_metadata_tmpDir h.ipv4.srcAddr
	jmp LABEL_END_1
	LABEL_FALSE_0 :	mov m.local_metadata_tmpDir h.ipv4.dstAddr
	LABEL_END_1 :	jmpnv LABEL_END_2 h.ipv4
	table ipv4_da_lpm
	LABEL_END_2 :	emit h.ethernet
	emit h.ipv4
	tx m.pna_main_output_metadata_output_port
}

