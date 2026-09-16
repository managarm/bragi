#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <varint.bragi.frg.hpp>
#else
#include <varint.bragi.std.hpp>
#endif

#include <cassert>

int main() {
	auto v = test::make_msg<Values>();
	v.set_seven_bytes(1ull << 48);
	v.set_eight_bytes_low(1ull << 49);
	v.set_eight_bytes_high((1ull << 56) - 1);
	v.set_nine_bytes(1ull << 56);
	v.set_negative(-1);

	auto t1 = test::make_msg<Test1>();
	t1.set_values(v);

	std::vector<std::byte> head_buf(256);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test1>(head_buf);
	assert(t2);

	assert(t2->values().seven_bytes() == 1ull << 48);
	assert(t2->values().eight_bytes_low() == 1ull << 49);
	assert(t2->values().eight_bytes_high() == (1ull << 56) - 1);
	assert(t2->values().nine_bytes() == 1ull << 56);
	assert(t2->values().negative() == -1);
}
