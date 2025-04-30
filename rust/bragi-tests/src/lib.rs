#[cfg(test)]
bragi::include_binding! {
    mod arrays_bragi = "arrays.rs",
    mod basic_bragi = "basic.rs",
    mod empty_bragi = "empty.rs",
    mod enums_bragi = "enums.rs",
    mod group_bragi = "group.rs",
    mod preamble_bragi = "preamble.rs",
    mod structs_bragi = "struct.rs",
    mod using_bragi = "using.rs",
}

#[cfg(test)]
mod arrays {
    use super::arrays_bragi::*;

    use bragi::Message;
    use std::io::Cursor;

    #[test]
    fn test1() {
        let msg = Test1::new(vec![0xDE, 0xAD, 0xBE, 0xEF]);
        assert_eq!(Test1::MESSAGE_ID, 1);
        assert_eq!(Test1::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test1 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.arr(), &[0xDE, 0xAD, 0xBE, 0xEF]);
    }

    #[test]
    fn test2() {
        let msg = Test2::new([0xDE, 0xAD, 0xBE, 0xEF, 0xFF]);
        assert_eq!(Test2::MESSAGE_ID, 2);
        assert_eq!(Test2::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test2 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.arr(), &[0xDE, 0xAD, 0xBE, 0xEF, 0xFF]);
    }

    #[test]
    fn test3() {
        let msg = Test3::new(vec![
            vec![0xDE, 0xAD, 0xBE, 0xEF],
            vec![0xCA, 0xFE, 0xBA, 0xBE],
            vec![0xB1, 0x6B, 0x00, 0xB5],
        ]);
        assert_eq!(Test3::MESSAGE_ID, 3);
        assert_eq!(Test3::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test3 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.arr().len(), 3);
        assert_eq!(msg.arr()[0], &[0xDE, 0xAD, 0xBE, 0xEF]);
        assert_eq!(msg.arr()[1], &[0xCA, 0xFE, 0xBA, 0xBE]);
        assert_eq!(msg.arr()[2], &[0xB1, 0x6B, 0x00, 0xB5]);
    }

    #[test]
    fn test4() {
        let msg = Test4::new(
            vec![
                [0xDE, 0xAD, 0xBE, 0xEF, 0xFF],
                [0xCA, 0xFE, 0xBA, 0xBE, 0xFF],
                [0xB1, 0x6B, 0x00, 0xB5, 0xFF],
            ],
            [
                vec![0xDE, 0xAD, 0xBE, 0xEF],
                vec![0xCA, 0xFE, 0xBA, 0xBE],
                vec![0xB1, 0x6B, 0x00, 0xB5],
                vec![],
                vec![],
            ],
        );
        assert_eq!(Test4::MESSAGE_ID, 4);
        assert_eq!(Test4::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test4 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.arr1().len(), 3);
        assert_eq!(msg.arr1()[0], [0xDE, 0xAD, 0xBE, 0xEF, 0xFF]);
        assert_eq!(msg.arr1()[1], [0xCA, 0xFE, 0xBA, 0xBE, 0xFF]);
        assert_eq!(msg.arr1()[2], [0xB1, 0x6B, 0x00, 0xB5, 0xFF]);
        assert_eq!(msg.arr2().len(), 5);
        assert_eq!(msg.arr2()[0], &[0xDE, 0xAD, 0xBE, 0xEF]);
        assert_eq!(msg.arr2()[1], &[0xCA, 0xFE, 0xBA, 0xBE]);
        assert_eq!(msg.arr2()[2], &[0xB1, 0x6B, 0x00, 0xB5]);
        assert_eq!(msg.arr2()[3], &[]);
        assert_eq!(msg.arr2()[4], &[]);
    }

    #[test]
    fn test5() {
        let msg = Test5::new([
            [0xDE, 0xAD, 0xBE, 0xEF],
            [0xCA, 0xFE, 0xBA, 0xBE],
            [0xB1, 0x6B, 0x00, 0xB5],
            [0xDE, 0xAD, 0xBE, 0xEF],
        ]);
        assert_eq!(Test5::MESSAGE_ID, 5);
        assert_eq!(Test5::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test5 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(
            msg.arr(),
            &[
                [0xDE, 0xAD, 0xBE, 0xEF],
                [0xCA, 0xFE, 0xBA, 0xBE],
                [0xB1, 0x6B, 0x00, 0xB5],
                [0xDE, 0xAD, 0xBE, 0xEF],
            ]
        );
    }
}

#[cfg(test)]
mod basic {
    use super::basic_bragi::*;

    use bragi::Message;
    use std::io::Cursor;

    #[test]
    fn basic_test() {
        let mut msg = Test::new(0xDEADBEEF, 0xDEADBEEFCAFEBABE, "Hello, world!".into());
        msg.set_d(1337);
        msg.set_e(vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 0]);

        assert_eq!(Test::MESSAGE_ID, 1);
        assert_eq!(Test::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.a(), 0xDEADBEEF);
        assert_eq!(msg.b(), 0xDEADBEEFCAFEBABE);
        assert_eq!(msg.c(), "Hello, world!");
        assert_eq!(msg.d(), Some(1337));
        assert_eq!(msg.e(), Some(&[1, 2, 3, 4, 5, 6, 7, 8, 9, 0][..]));
        assert_eq!(msg.f(), None);
    }
}

#[cfg(test)]
mod empty {
    use super::empty_bragi::*;

    use bragi::Message;
    use std::io::Cursor;

    #[test]
    fn empty_head() {
        let msg = TestEmptyHead::new("Empty head".into());
        assert_eq!(TestEmptyHead::MESSAGE_ID, 1);
        assert_eq!(TestEmptyHead::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_head(), 8);
        assert!(msg.size_of_tail() > 0);

        let (head, tail) = bragi::write_head_tail(&msg).unwrap();
        assert_eq!(head.len(), msg.size_of_head());
        assert_eq!(tail.len(), msg.size_of_tail());

        let msg: TestEmptyHead =
            bragi::read_head_tail(&mut Cursor::new(&head), &mut Cursor::new(&tail)).unwrap();
        assert_eq!(msg.foo(), "Empty head");
    }

    #[test]
    fn empty_tail() {
        let msg = TestEmptyTail::new("Empty tail".into());
        assert_eq!(TestEmptyTail::MESSAGE_ID, 2);
        assert_eq!(TestEmptyTail::HEAD_SIZE, 128);
        assert!(msg.size_of_head() > 8);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: TestEmptyTail = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.foo(), "Empty tail");
    }

    #[test]
    fn no_tail() {
        let msg = TestNoTail::new("No tail".into());
        assert_eq!(TestNoTail::MESSAGE_ID, 3);
        assert_eq!(TestNoTail::HEAD_SIZE, 128);
        assert!(msg.size_of_head() > 8);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: TestNoTail = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.foo(), "No tail");
    }

    #[test]
    fn empty_message() {
        let msg = TestEmptyMessage::new();
        assert_eq!(TestEmptyMessage::MESSAGE_ID, 4);
        assert_eq!(TestEmptyMessage::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_head(), 8);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let _msg: TestEmptyMessage = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
    }
}

#[cfg(test)]
mod enums {
    use super::enums_bragi::*;

    use bragi::Message;
    use std::io::Cursor;

    #[test]
    fn enums_test() {
        let msg = Test::new(
            Foo::D,
            Bar::E,
            vec![Foo::D, Foo::A, Foo::F, Foo::B],
            [Bar::E, Bar::B, Bar::A, Bar::C],
        );
        assert_eq!(Test::MESSAGE_ID, 1);
        assert_eq!(Test::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        assert_eq!(Foo::A as u8, 1);
        assert_eq!(Foo::B as u8, 2);
        assert_eq!(Foo::C as u8, 4);
        assert_eq!(Foo::D as u8, 5);
        assert_eq!(Foo::E as u8, 6);
        assert_eq!(Foo::F as u8, 7);

        assert_eq!(Bar::A.value(), 1);
        assert_eq!(Bar::B.value(), 2);
        assert_eq!(Bar::C.value(), 4);
        assert_eq!(Bar::D.value(), 2);
        assert_eq!(Bar::E.value(), 3);
        assert_eq!(Bar::F.value(), 4);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.foo(), Foo::D);
        assert_eq!(msg.bar(), Bar::E);
        assert_eq!(msg.foos(), &[Foo::D, Foo::A, Foo::F, Foo::B]);
        assert_eq!(msg.bars(), &[Bar::E, Bar::B, Bar::A, Bar::C]);
    }
}

#[cfg(test)]
mod group {
    use super::group_bragi::*;

    use bragi::Message;

    #[test]
    fn group_test() {
        assert_eq!(Test1::MESSAGE_ID, 1);
        assert_eq!(Test2::MESSAGE_ID, 1);
        assert_eq!(Test3::MESSAGE_ID, 1);
    }
}

#[cfg(test)]
mod preamble {
    use super::preamble_bragi::*;

    use bragi::Message;
    use std::io::Cursor;

    #[test]
    fn test_foo() {
        let msg = Foo::new("Hello...".into());
        assert_eq!(Foo::MESSAGE_ID, 1);
        assert_eq!(Foo::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let preamble = bragi::read_preamble(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(preamble.id(), Foo::MESSAGE_ID);
        assert_eq!(preamble.tail_size(), 0);

        let msg: Foo = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        assert_eq!(msg.foo(), "Hello...");
    }

    #[test]
    fn test_bar() {
        let msg = Bar::new("..world!".into(), 123456789);
        assert_eq!(Bar::MESSAGE_ID, 2);
        assert_eq!(Bar::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 4);

        let (head, tail) = bragi::write_head_tail(&msg).unwrap();
        let preamble = bragi::read_preamble(&mut Cursor::new(&head)).unwrap();
        assert_eq!(preamble.id(), Bar::MESSAGE_ID);
        assert_eq!(preamble.tail_size(), 4);

        let msg: Bar =
            bragi::read_head_tail(&mut Cursor::new(&head), &mut Cursor::new(&tail)).unwrap();
        assert_eq!(msg.bar(), "..world!");
        assert_eq!(msg.baz(), 123456789);
    }
}

#[cfg(test)]
mod structs {
    use super::structs_bragi::*;

    use bragi::Message;
    use std::io::Cursor;

    #[test]
    fn test1() {
        let foo = Foo::new(
            "Hello".into(),
            0xDEADBEEFCAFEBABE,
            0xDEADBEEF,
            vec![1, 2, 3, 4],
        );
        let msg = Test1::new(foo);
        assert_eq!(Test1::MESSAGE_ID, 1);
        assert_eq!(Test1::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test1 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        let foo = msg.foo();
        assert_eq!(foo.a(), "Hello");
        assert_eq!(foo.b(), 0xDEADBEEFCAFEBABE);
        assert_eq!(foo.c(), 0xDEADBEEF);
        assert_eq!(foo.d(), &[1, 2, 3, 4]);
    }

    #[test]
    fn test2() {
        let bar1 = Bar::new("Hello".into(), 1);
        let bar2 = Bar::new("World".into(), 2);
        let msg = Test2::new(vec![bar1, bar2]);
        assert_eq!(Test2::MESSAGE_ID, 2);
        assert_eq!(Test2::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test2 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        let bars = msg.bars();
        assert_eq!(bars.len(), 2);
        assert_eq!(bars[0].a(), "Hello");
        assert_eq!(bars[1].a(), "World");
        assert_eq!(bars[0].b(), 1);
        assert_eq!(bars[1].b(), 2);
    }

    #[test]
    fn test3() {
        let bar = Bar::new("Hello".into(), 1);
        let foo1 = Foo::new(
            "World".into(),
            0xDEADBEEFCAFEBABE,
            0xDEADBEEF,
            vec![1, 2, 3, 4],
        );
        let foo2 = Foo::new(
            "Testing".into(),
            1234567801234567890,
            0xCAFEBABE,
            vec![5, 6, 7, 8],
        );
        let baz = Baz::new(bar, vec![foo1, foo2]);
        let msg = Test3::new(baz);
        assert_eq!(Test3::MESSAGE_ID, 3);
        assert_eq!(Test3::HEAD_SIZE, 128);
        assert_eq!(msg.size_of_tail(), 0);

        let buffer = bragi::write_head_only(&msg).unwrap();
        let msg: Test3 = bragi::read_head_only(&mut Cursor::new(&buffer)).unwrap();
        let baz = msg.baz();
        let bar = baz.bar();
        let foos = baz.foos();
        assert_eq!(bar.a(), "Hello");
        assert_eq!(bar.b(), 1);
        assert_eq!(foos.len(), 2);
        assert_eq!(foos[0].a(), "World");
        assert_eq!(foos[1].a(), "Testing");
        assert_eq!(foos[0].b(), 0xDEADBEEFCAFEBABE);
        assert_eq!(foos[1].b(), 1234567801234567890);
        assert_eq!(foos[0].c(), 0xDEADBEEF);
        assert_eq!(foos[1].c(), 0xCAFEBABE);
        assert_eq!(foos[0].d(), &[1, 2, 3, 4]);
        assert_eq!(foos[1].d(), &[5, 6, 7, 8]);
    }
}
