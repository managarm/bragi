#pragma once

#include <bragi/internals.hpp>
#include <frg/optional.hpp>
#include <stddef.h>

namespace bragi {

template <template<typename> typename Message, typename Allocator, typename HBuffer, typename TBuffer>
inline frg::optional<Message<Allocator>> parse_head_tail(const HBuffer &head, const TBuffer &tail, Allocator allocator) {
	Message<Allocator> msg{allocator};

	limited_reader head_rd{head.data(), head.size()};
	limited_reader tail_rd{tail.data(), tail.size()};

	if (!msg.decode_head(head_rd))
		return frg::null_opt;
	if (!msg.decode_tail(tail_rd))
		return frg::null_opt;

	return msg;
}

template <template<typename> typename Message, typename Allocator, typename HBuffer>
inline frg::optional<Message<Allocator>> parse_head_only(const HBuffer &head, Allocator allocator) {
	Message<Allocator> msg{allocator};

	limited_reader head_rd{head.data(), head.size()};

	if (!msg.decode_head(head_rd))
		return frg::null_opt;

	return msg;
}

namespace detail {
	struct dummy_allocator {
		void *allocate(size_t);
		void deallocate(void *, size_t);
	};
} // namespace detail

template<template<typename> typename Message>
inline constexpr auto message_id = Message<detail::dummy_allocator>::message_id;

template<template<typename> typename Message>
inline constexpr auto head_size = Message<detail::dummy_allocator>::head_size;

} // namespace bragi
