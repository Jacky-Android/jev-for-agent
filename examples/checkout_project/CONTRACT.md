# Synthetic checkout fixture

`discount` is a fraction of the complete order subtotal. `test_fractional_discount` is a required core checkout validation in this synthetic project. Values and expectations are fixture data, not user project facts.

`order_before.py` preserves the original buggy source; `order.py` is the Agent repair. Copy only order.py and test_order.py to a scratch directory to run. To reproduce the failure, replace the scratch order.py with order_before.py. Do not overwrite an actual project.
