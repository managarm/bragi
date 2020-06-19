#pragma once

#include <bragi/internals.hpp>
#include <optional>

namespace bragi {

template <typename Message, typename HBuffer, typename TBuffer>
inline std::optional<Message> parse_head_tail(const HBuffer &head, const TBuffer &tail) {
	Message msg;

	limited_reader head_rd{head.data(), head.size()};
	limited_reader tail_rd{tail.data(), tail.size()};

	if (!msg.decode_head(head_rd))
		return std::nullopt;
	if (!msg.decode_tail(tail_rd))
		return std::nullopt;

	return msg;
}

template <typename Message, typename HBuffer>
inline std::optional<Message> parse_head_only(const HBuffer &head) {
	Message msg;

	limited_reader head_rd{head.data(), head.size()};

	if (!msg.decode_head(head_rd))
		return std::nullopt;

	return msg;
}


template<typename Message>
inline constexpr auto message_id = Message::message_id;

} // namespace bragi
