def generate_proposal(self, opportunity_id, include_addons, include_bundles, payment_schedule, custom_milestones, include_assessments):
    proposal = {'total_amount': 0, 'currency': 'MXN', 'modalities': []}
    for bundle in include_bundles:
        bu = bundle['business_unit']
        base_salary = bundle['base_salary']
        retainer_scheme = bundle.get('retainer_scheme')
        modalities = []
        for mode in ['ai', 'hybrid', 'human']:
            count = bundle.get(mode, 0)
            if count == 0:
                continue
            cost = 0
            milestones = []
            # Obtener precios y porcentajes dinámicamente
            plan = self.get_plan(bu, mode)  # Debe devolver dict con 'base_price', 'rate', etc.
            if mode == 'ai':
                cost = plan['base_price'] * count
                milestones = [{'label': 'Pago único', 'amount': cost, 'detail': '100% al inicio'}]
            elif mode in ['hybrid', 'human'] and bu in ['huntRED Executive', 'huntRED Standard']:
                base_calc = base_salary * 13
                rate = plan['rate_discount'] if count >= 2 else plan['rate']
                cost = base_calc * rate * count
                if retainer_scheme == 'single':
                    retainer = cost * 0.25
                    remainder = cost * 0.75
                    milestones = [
                        {'label': 'Retainer', 'amount': retainer, 'detail': '1 pago de 25%'},
                        {'label': 'Al éxito 1', 'amount': remainder / 2, 'detail': '37.5% en colocación'},
                        {'label': 'Al éxito 2', 'amount': remainder / 2, 'detail': '37.5% en colocación final'}
                    ]
                else:  # double
                    retainer = cost * 0.175
                    remainder = cost * 0.65
                    milestones = [
                        {'label': 'Retainer 1', 'amount': retainer, 'detail': '17.5%'},
                        {'label': 'Retainer 2', 'amount': retainer, 'detail': '17.5%'},
                        {'label': 'Al éxito', 'amount': remainder, 'detail': '65% en colocación'}
                    ]
            else:  # huntU, amigro
                cost = plan['base_price'] * count
                milestones = [{'label': 'Pago único', 'amount': cost, 'detail': '100% al inicio'}]
            modalities.append({'type': mode, 'count': count, 'cost': cost, 'billing_milestones': milestones})
            proposal['total_amount'] += cost
        proposal['modalities'].extend(modalities)
    return proposal 