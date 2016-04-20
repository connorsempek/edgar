
#------------------------------------------------------------------------------
# imports

import re
import requests
import pandas as pd


#------------------------------------------------------------------------------
# parent class with base url info

class EDGAR(object):

	def __init__(self, action):

		self.search_url = 'http://www.sec.gov/cgi-bin/browse-edgar'
		self.archive_url = 'https://www.sec.gov/Archives/edgar/data/'
		self.action = action


#------------------------------------------------------------------------------
# Company subclass, searches company filings using SEC EDGAR web search

class Company(EDGAR):

	def __init__(self, cik, owner='exclude', form=None, max_date=None):
		'''get company meta data regarding SEC filings

		Parameters
		----------
			cik   : (str) can be CIK or ticker symbol of a public company
			owner : (str) valid values passed are `include`, `exclude`, `only`
			form  : (str) any valid SEC filing, e.g., 10-K, 4. If none, then
					a filing history of all forms will be instantiated.  
		'''

		# instantiate parent class
		EDGAR.__init__(self, action='getcompany')

		# instantiate user params
		self.cik = cik
		self.owner = owner
		self.form = form
		self.max_date = max_date
		self.params = {
			'CIK'    : self.cik,
			'action' : self.action,
			'owner'  : self.owner,
			'dateb'  : self.max_date,
			'type'   : self.form,
			}

		# get all search results
		self.search_results = self._search_results_text()

		# get true cik if input cik is ticker
		if self.cik.isalpha():
			self.ticker = self.cik
			self.cik = self._get_cik()
			self.params['CIK'] = self.cik

		# filing history as data frame
		self.filings = self._filing_history()

		# urls to html files of filings
		self._add_filing_urls()


	def _search_results_text(self):

		MAX = 10 ** 6
		CHECK_STR = 'Acc-no'
		PAGE_LIMIT = 100 # current site returned results max
		
		params = self.params
		params.update({'count': PAGE_LIMIT})
		search_results = []
		for i in xrange(MAX):
			params.update({'start': i * PAGE_LIMIT})
			r = requests.get(url=self.search_url, params=self.params)
			search_results.append(r.text)
			if r.text.count(CHECK_STR) < PAGE_LIMIT:
				break
		return search_results


	def _get_cik(self):

		res = self.search_results[0]
		return res.split('</head>')[0].split('CIK=')[-1].split('&')[0]


	def _filing_history(self):

		tbls = [pd.read_html(res, header=0)[-1] for res in self.search_results]
		filings = pd.concat(tbls)

		# add accession number column
		acc_no = lambda s: s.split('Acc-no:')[1].split()[0].strip()
		filings['AccessionNo'] = filings.Description.apply(acc_no)

		# remove accession number from description column
		desc = lambda s: s.split('Acc-no:')[0]
		filings['Description'] = filings.Description.apply(desc)

		# clean up 
		filings.drop('Format', axis=1, inplace=True)
		col_map = {
			'File/Film Number' : 'FilmNo',
			'Filed/Effective'  : 'EffectiveDate',
			'Filing Date'      : 'FilingDate',
			}
		filings.rename(columns=col_map, inplace=True)
		filings.index = range(filings.shape[0])
		return filings


	def _add_filing_urls(self):

		self.filings['URL'] = (''
			+ self.archive_url
			+ self.cik.lstrip('0') 
			+ '/'
			+ self.filings.AccessionNo.str.replace('-', '')
			+ '/'
			+ self.filings.AccessionNo
			+ '.txt'
			)
		

	def get_filing(self, form, ):
		pass



#------------------------------------------------------------------------------
# testing

if __name__ == '__main__':
	
ticker = 'tsla'
tsla = Company(ticker)
filings = tsla.filings
