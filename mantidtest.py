import pytest
import numpy
import mantid
import mantid.simpleapi



def main():
    returns = pytest.main(['-vv --cov', 'MJOLNIR'])

    return returns

if __name__ == '__main__':
    import sys
    instanceId = main()
    sys.exit(instanceId)


