#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <bitfield.bragi.frg.hpp>
#else
#include <bitfield.bragi.std.hpp>
#endif

#include <cassert>

int main() {
	auto h = test::make_msg<Holder>();
	h.set_f8(Flags8::A | Flags8::C);
	h.set_f32(Flags32::D | Flags32::E);
	h.set_f64(Flags64::F | Flags64::G);

	auto t1 = test::make_msg<Test1>();
	t1.set_f8(Flags8::B);
	t1.set_f32(Flags32::E);
	t1.set_f64(Flags64::G);
	t1.set_holder(h);

	std::vector<std::byte> head_buf(128);
	assert(bragi::write_head_only(t1, head_buf));

	auto t2 = test::parse_with<Test1>(head_buf);
	assert(t2);

	assert(t2->f8() == Flags8::B);
	assert(t2->f32() == Flags32::E);
	assert(t2->f64() == Flags64::G);
	assert(t2->holder().f8() == (Flags8::A | Flags8::C));
	assert(t2->holder().f32() == (Flags32::D | Flags32::E));
	assert(t2->holder().f64() == (Flags64::F | Flags64::G));
}
