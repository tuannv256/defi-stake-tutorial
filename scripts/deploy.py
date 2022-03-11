import json
import os
import shutil
from scripts.helpful_scripts import get_account, get_contract
from brownie import DappToken, TokenFarm, config, network
from web3 import Web3
import yaml

KEPT_BALANCE = Web3.toWei(100, "ether")


def deploy_token_farm_and_dapp_token(transfer_front_end=False):
    account = get_account()
    dapp_token = DappToken.deploy({"from": account})
    token_farm = TokenFarm.deploy(
        dapp_token.address, {"from": account}, publish_source=config["networks"][network.show_active()]["verify"]
    )
    tx = dapp_token.transfer(token_farm.address, dapp_token.totalSupply() - KEPT_BALANCE, {"from": account})
    tx.wait(1)
    weth_token = get_contract("weth_token")
    fau_token = get_contract("fau_token")
    allowed_token_map = {
        dapp_token: get_contract("dai_usd_price_feed"),
        fau_token: get_contract("dai_usd_price_feed"),
        weth_token: get_contract("eth_usd_price_feed"),
    }
    add_allowed_token(token_farm, allowed_token_map, account)
    if transfer_front_end:
        update_front_end()
    return token_farm, dapp_token


def add_allowed_token(token_farm, allowed_token_map, account):
    for token in allowed_token_map:
        add_tx = token_farm.addAllowedTokens(token.address, {"from": account})
        add_tx.wait(1)
        set_tx = token_farm.setPriceFeedContract(token.address, allowed_token_map[token], {"from": account})
        set_tx.wait(1)
    return token_farm


def update_front_end():
    copy_folders_to_front_end("./build", "./front_end/src/chain-info")
    with open("brownie-config.yaml", "r") as brownie_config:
        config_map = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open("./front_end/src/brownie-config.json", "w") as brownie_config_json:
            json.dump(config_map, brownie_config_json)
    print("Front end updated!")


def copy_folders_to_front_end(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def main():
    deploy_token_farm_and_dapp_token(update_front_end=True)
