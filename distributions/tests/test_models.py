import os
import glob
from nose.tools import assert_true, assert_in
import random
from distributions.tests.util import assert_hasattr, assert_close, import_model

MODULES = {}
ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
for path in glob.glob(os.path.join(ROOT, 'models', '*.p*')):
    filename = os.path.split(path)[-1]
    name = os.path.splitext(filename)[0]
    if not name.startswith('__'):
        module = import_model(name)
        MODULES[name] = module


def iter_examples(Model):
    assert_hasattr(Model, 'EXAMPLES')
    EXAMPLES = Model.EXAMPLES
    assert_true(EXAMPLES, 'no examples provided')
    for i, EXAMPLE in enumerate(EXAMPLES):
        print 'testing example {}/{}'.format(1 + i, len(Model.EXAMPLES))
        assert_in('model', EXAMPLE)
        assert_in('values', EXAMPLE)
        yield EXAMPLE


def test_interface():
    for name in MODULES:
        yield _test_interface, name


def _test_interface(name):
    module = MODULES[name]
    assert_hasattr(module, 'Model')
    Model = module.Model

    for EXAMPLE in iter_examples(Model):
        model = Model.load_model(EXAMPLE['model'])
        values = EXAMPLE['values']
        group1 = model.Group()
        group2 = model.Group()

        model.group_init(group1)
        model.group_init(group2)
        for value in values:
            model.group_add_value(group1, value)
            model.group_add_value(group2, value)
        for value in values:
            model.group_remove_value(group2, value)
        model.group_merge(group2, group1)

        for value in values:
            model.score_value(group1, value)
        for _ in xrange(10):
            value = model.sample_value(group1)
            model.score_value(group1, value)
            model.sample_group(10)
        model.score_group(group1)
        model.score_group(group2)

        assert_close(model.dump(), EXAMPLE['model'])
        assert_close(model.dump(), Model.dump_model(model))
        assert_close(group1.dump(), Model.dump_group(group1))


def add_remove_add(name):
    '''
    Test group_add_value, group_remove_value, pred_prob, data_prob
    '''
    Model = MODULES[name].Model
    DATA_COUNT = 20

    for EXAMPLE in iter_examples(Model):

        model = Model.load_model(EXAMPLE['model'])
        #model.realize()
        #values = model['values'][:]

        values = []
        group = model.Group()
        model.group_init(group)
        score = 0
        for _ in range(DATA_COUNT):
            value = model.sample_value(group)
            values.append(value)
            score += model.score_value(group, value)
            model.group_add_value(group, value)

        group_all = model.load_group(model.dump_group(group))
        assert_close(
            score,
            model.score_group(group),
            err_msg='p(x1,...,xn) != p(x1) p(x2|x1) p(xn|...)')

        random.shuffle(values)

        for value in values:
            model.group_remove_value(group, value)

        group_empty = model.Group()
        model.group_init(group_empty)
        assert_close(
            group.dump(),
            group_empty.dump(),
            err_msg='group + values - values != group')

        random.shuffle(values)
        for value in values:
            model.group_add_value(group, value)
        assert_close(
            group.dump(),
            group_all.dump(),
            err_msg='group - values + values != group')


def test_add_remove_add():
    for name in MODULES:
        yield add_remove_add, name