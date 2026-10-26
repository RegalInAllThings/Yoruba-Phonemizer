import argparse
from yorubag2p_prototype import YorubaConverter

p = argparse.ArgumentParser(description='Rule-based Yoruba G2P prototype')
p.add_argument('text', nargs='+', help='Yoruba text to convert')
a = p.parse_args()
print(YorubaConverter().text(' '.join(a.text)))
