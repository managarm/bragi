#pragma once

#include <bragi/internals.hpp>

namespace bragi {

// Takes a forwarding reference to be compatible with both containers and spans.
template <typename Message, typename HBuffer, typename TBuffer>
inline bool write_head_tail(Message &msg, HBuffer &&head, TBuffer &&tail) {
	limited_writer head_rd{head.data(), head.size()};
	limited_writer tail_rd{tail.data(), tail.size()};

	if (!msg.encode_head(head_rd))
		return false;

	return msg.encode_tail(tail_rd);
}

// Takes a forwarding reference to be compatible with both containers and spans.
template <typename Message, typename HBuffer>
inline bool write_head_only(Message &msg, HBuffer &&head) {
	limited_writer head_rd{head.data(), head.size()};

	return msg.encode_head(head_rd);
}

} // namespace bragi
