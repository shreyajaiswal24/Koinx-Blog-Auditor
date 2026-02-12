"""Fetch and parse tax law reference data from IRS.gov."""

import logging
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from config.settings import IRS_SOURCES

logger = logging.getLogger(__name__)

# Hardcoded authoritative tax reference data that supplements live IRS scraping.
# This ensures the auditor has accurate baseline knowledge even if IRS pages
# change structure or become temporarily unavailable.
AUTHORITATIVE_TAX_RULES = {
    "capital_gains_rates": {
        "topic": "Capital Gains Tax Rates",
        "rules": [
            "Short-term capital gains (held ≤ 1 year) are taxed as ordinary income.",
            "Long-term capital gains (held > 1 year) are taxed at 0%, 15%, or 20% depending on taxable income.",
            "Net Investment Income Tax (NIIT) of 3.8% applies to high earners (MAGI > $200K single, $250K married filing jointly).",
            "The holding period starts the day after acquisition and includes the day of disposition.",
        ],
        "source": "IRS Publication 544, IRC §1222",
    },
    "crypto_as_property": {
        "topic": "Cryptocurrency as Property",
        "rules": [
            "Virtual currency is treated as property for federal tax purposes (IRS Notice 2014-21).",
            "General tax principles applicable to property transactions apply to cryptocurrency.",
            "Cryptocurrency is NOT treated as currency for tax purposes.",
            "Each disposal of cryptocurrency is a taxable event requiring gain/loss calculation.",
        ],
        "source": "IRS Notice 2014-21, Rev. Rul. 2019-24",
    },
    "cost_basis_methods": {
        "topic": "Cost Basis Identification Methods",
        "rules": [
            "Specific identification is allowed if you can identify the specific units sold.",
            "FIFO (First In, First Out) is the default method if specific identification is not used.",
            "Starting January 1, 2025, brokers must use per-wallet/per-account basis tracking.",
            "Under the 2024 final regulations (TD 10000), the default method for CeFi broker transactions is FIFO unless the taxpayer elects otherwise.",
            "HIFO (Highest In, First Out) and LIFO are allowed ONLY with specific identification.",
        ],
        "source": "IRS Final Regulations TD 10000 (2024), IRC §1012",
    },
    "broker_reporting_1099da": {
        "topic": "Broker Reporting — Form 1099-DA",
        "rules": [
            "Starting 2025 tax year, centralized exchanges (CeFi brokers) must report digital asset transactions on Form 1099-DA.",
            "Form 1099-DA replaces previous 1099-B reporting for digital assets.",
            "DeFi broker reporting requirements begin in 2027 (per final regulations issued Dec 2024).",
            "Brokers must report: gross proceeds, date of sale, and (if available) cost basis.",
            "Real estate transactions involving digital assets over $10,000 must be reported starting 2025.",
        ],
        "source": "IRS Final Regulations TD 10000 (2024), Infrastructure Investment and Jobs Act §80603",
    },
    "taxable_events": {
        "topic": "Taxable Events for Cryptocurrency",
        "rules": [
            "Selling crypto for fiat currency is a taxable event.",
            "Trading one cryptocurrency for another is a taxable event.",
            "Using crypto to purchase goods or services is a taxable event.",
            "Receiving crypto as payment for services is ordinary income at FMV on date of receipt.",
            "Mining rewards are ordinary income at FMV when received.",
            "Staking rewards are ordinary income at FMV when the taxpayer gains dominion and control.",
            "Airdrops are ordinary income at FMV when received (Rev. Rul. 2019-24).",
            "Hard forks without an airdrop are NOT taxable events.",
            "Transferring crypto between your own wallets is NOT a taxable event.",
        ],
        "source": "IRS Notice 2014-21, Rev. Rul. 2019-24, Rev. Rul. 2023-14",
    },
    "reporting_requirements": {
        "topic": "Tax Reporting Requirements",
        "rules": [
            "Digital asset transactions must be reported on Form 8949 and Schedule D.",
            "The Form 1040 includes a digital asset question that must be answered by all filers.",
            "Failure to report can result in penalties including accuracy-related penalties (20%) and fraud penalties (75%).",
            "Foreign crypto exchange accounts may trigger FBAR (FinCEN 114) if aggregate value exceeds $10,000.",
            "FATCA (Form 8938) may apply for foreign digital asset accounts above threshold amounts.",
        ],
        "source": "IRS Form 8949, Schedule D, FinCEN guidance",
    },
    "defi_and_nfts": {
        "topic": "DeFi and NFT Taxation",
        "rules": [
            "Providing liquidity to DeFi protocols may trigger taxable events when tokens are swapped.",
            "Yield farming rewards are generally ordinary income at FMV when received.",
            "NFT sales are subject to capital gains tax; collectible NFTs may be taxed at the 28% collectibles rate.",
            "Wrapping/unwrapping tokens (e.g., ETH→WETH) — IRS has not issued specific guidance; conservative position treats it as taxable.",
            "Governance token rewards are ordinary income at FMV.",
        ],
        "source": "IRS general property taxation principles, proposed regulations",
    },
    "wash_sale_rule": {
        "topic": "Wash Sale Rule and Crypto",
        "rules": [
            "As of 2024, the wash sale rule (IRC §1091) does NOT explicitly apply to cryptocurrency.",
            "The wash sale rule applies to stocks and securities; crypto is classified as property, not a security.",
            "However, proposed legislation and IRS rulemaking may extend wash sale rules to digital assets in the future.",
            "Starting 2025, some tax professionals advise caution as regulatory changes are anticipated.",
        ],
        "source": "IRC §1091, IRS Notice 2014-21",
    },
}


class IRSFetcher:
    """Fetches tax reference information from IRS.gov pages."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "KoinX-Tax-Auditor/1.0 (educational-research)",
            "Accept": "text/html",
        })

    def fetch_all_references(self) -> List[Dict[str, str]]:
        """Fetch all IRS reference data and combine with authoritative rules.

        Returns a list of dicts with keys: topic, content, source, url.
        """
        references = []

        # Start with authoritative hardcoded rules (always available)
        for key, rule_set in AUTHORITATIVE_TAX_RULES.items():
            references.append({
                "topic": rule_set["topic"],
                "content": "\n".join(f"- {r}" for r in rule_set["rules"]),
                "source": rule_set["source"],
                "url": "",
            })

        # Supplement with live IRS page content
        for source_key, url in IRS_SOURCES.items():
            content = self._fetch_page_content(url)
            if content:
                references.append({
                    "topic": f"IRS: {source_key.replace('_', ' ').title()}",
                    "content": content[:5000],  # limit per source
                    "source": f"IRS.gov ({url})",
                    "url": url,
                })

        logger.info(f"Compiled {len(references)} tax reference entries")
        return references

    def _fetch_page_content(self, url: str) -> str:
        """Fetch and extract text content from an IRS page."""
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Remove nav, header, footer
            for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
                tag.decompose()

            # Try to find main content area
            main = soup.find("main") or soup.find("div", {"id": "main-content"}) or soup
            text = main.get_text(separator="\n", strip=True)

            # Clean up
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            return "\n".join(lines)

        except requests.RequestException as e:
            logger.warning(f"Failed to fetch IRS page {url}: {e}")
            return ""
