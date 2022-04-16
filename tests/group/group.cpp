#include <iostream>

#include "../test-util.hpp"

#ifdef TEST_FRIGG
#include <group.bragi.frg.hpp>
#else
#include <group.bragi.std.hpp>
#endif

#include <cassert>

static_assert(bragi::message_id<Test1> == 1);
static_assert(bragi::message_id<Test2> == 1);
static_assert(bragi::message_id<Test3> == 1);

int main() {
}
