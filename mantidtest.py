import pytest
import numpy
import mantid
import mantid.simpleapi



def main():
    returns = pytest.main(['-vv', 'MJOLNIR'])

    return returns

if __name__ == '__main__':
    main()


