#pragma once

#include <bragi/internals.hpp>
#include <frg/optional.hpp>

namespace bragi {

template <typename Message, typename HBuffer, typename TBuffer>
inline frg::optional<Message> parse_head_tail(const HBuffer &head, const TBuffer &tail) {
	Message msg;

	limited_reader head_rd{head.data(), head.size()};
	limited_reader tail_rd{tail.data(), tail.size()};

	if (!msg.decode_head(head_rd))
		return frg::null_opt;
	if (!msg.decode_tail(tail_rd))
		return frg::null_opt;

	return msg;
}

template <typename Message, typename HBuffer>
inline frg::optional<Message> parse_head_only(const HBuffer &head) {
	Message msg;

	limited_reader head_rd{head.data(), head.size()};

	if (!msg.decode_head(head_rd))
		return frg::null_opt;

	return msg;
}

template <typename Message, typename HBuffer, typename TBuffer>
inline bool write_head_tail(Message &msg, HBuffer &head, TBuffer &tail) {
	limited_writer head_rd{head.data(), head.size()};
	limited_writer tail_rd{tail.data(), tail.size()};

	if (!msg.encode_head(head_rd))
		return false;

	return msg.encode_tail(tail_rd);
}

template <typename Message, typename HBuffer>
inline bool write_head_only(Message &msg, HBuffer &head) {
	limited_writer head_rd{head.data(), head.size()};

	return msg.encode_head(head_rd);
}

} // namespace bragi
