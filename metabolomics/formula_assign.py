"""
Molecular Formula Assignment from m/z values
Tries both positive and negative ion modes
"""
import pandas as pd
import numpy as np
from itertools import product

# Exact masses of elements
MASSES = {
    'C': 12.000000,
    'H': 1.007825,
    'N': 14.003074,
    'O': 15.994915,
    'S': 31.972071,
    'P': 30.973762,
}

# Mass of electron (for ion mode correction)
ELECTRON_MASS = 0.000548579909

# Element limits (reasonable for metabolites)
LIMITS = {
    'C': (0, 50),
    'H': (0, 100),
    'N': (0, 10),
    'O': (0, 30),
    'S': (0, 5),
    'P': (0, 5),
}

def calc_mass(formula):
    """Calculate exact mass from formula dict"""
    return sum(MASSES[el] * count for el, count in formula.items())

def formula_to_string(formula):
    """Convert formula dict to string like C6H12O6"""
    parts = []
    for el in ['C', 'H', 'N', 'O', 'S', 'P']:
        if formula.get(el, 0) > 0:
            if formula[el] == 1:
                parts.append(el)
            else:
                parts.append(f"{el}{formula[el]}")
    return ''.join(parts) if parts else None

def check_rules(formula):
    """Apply basic chemical feasibility rules"""
    C = formula.get('C', 0)
    H = formula.get('H', 0)
    N = formula.get('N', 0)
    O = formula.get('O', 0)
    S = formula.get('S', 0)
    P = formula.get('P', 0)

    # Must have at least C or N
    if C == 0 and N == 0:
        return False

    # Hydrogen rule: H <= 2C + N + 2
    max_h = 2 * C + N + 2
    if H > max_h:
        return False

    # Nitrogen rule (odd/even)
    # For even electron ions, N should affect parity

    # O/C ratio check (usually < 2 for metabolites)
    if C > 0 and O / C > 2:
        return False

    # H/C ratio check (0.2 to 3.1 for metabolites)
    if C > 0:
        hc = H / C
        if hc < 0.2 or hc > 3.1:
            return False

    # Must have some hydrogen
    if H == 0 and C > 0:
        return False

    return True

def assign_formula(neutral_mass, ppm_tolerance=3):
    """Find molecular formulas matching the neutral mass"""
    matches = []

    # Rough filter: C gives ~12 Da each
    max_c = min(int(neutral_mass / 12) + 2, LIMITS['C'][1])

    for C in range(0, max_c + 1):
        # Remaining mass after carbons
        remaining = neutral_mass - C * MASSES['C']
        if remaining < 0:
            break

        max_h = min(int(remaining / MASSES['H']) + 2, LIMITS['H'][1])

        for N in range(LIMITS['N'][0], LIMITS['N'][1] + 1):
            for O in range(LIMITS['O'][0], LIMITS['O'][1] + 1):
                for S in range(LIMITS['S'][0], LIMITS['S'][1] + 1):
                    for P in range(LIMITS['P'][0], LIMITS['P'][1] + 1):
                        # Calculate H needed
                        partial_mass = (C * MASSES['C'] + N * MASSES['N'] +
                                       O * MASSES['O'] + S * MASSES['S'] +
                                       P * MASSES['P'])
                        h_needed = (neutral_mass - partial_mass) / MASSES['H']

                        # Check if H is reasonable integer
                        h_int = round(h_needed)
                        if h_int < 0 or h_int > LIMITS['H'][1]:
                            continue

                        formula = {'C': C, 'H': h_int, 'N': N, 'O': O, 'S': S, 'P': P}
                        calc = calc_mass(formula)

                        # Check ppm error
                        ppm_error = abs(calc - neutral_mass) / neutral_mass * 1e6

                        if ppm_error <= ppm_tolerance:
                            if check_rules(formula):
                                matches.append({
                                    'formula': formula_to_string(formula),
                                    'calc_mass': calc,
                                    'ppm_error': ppm_error
                                })

    # Sort by ppm error
    matches.sort(key=lambda x: x['ppm_error'])
    return matches

def main():
    # Read data
    print("Reading data...")
    df = pd.read_excel('Emily_Data_Pruned_Labeled.xlsx')

    # Get rows with neutral mass
    has_mass = df['Neutral mass (Da)'].notna()
    print(f"Total rows: {len(df)}")
    print(f"Rows with neutral mass: {has_mass.sum()}")

    # For rows without neutral mass, try to calculate from m/z
    # We'll try BOTH positive [M+H]+ and negative [M-H]- modes

    results = []
    proton_mass = MASSES['H'] - ELECTRON_MASS  # ~1.007276

    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"Processing row {idx}...")

        neutral = row['Neutral mass (Da)']
        mz = row['m/z']

        # If we have neutral mass, use it
        if pd.notna(neutral):
            target_mass = neutral
            mode_used = 'neutral'
        elif pd.notna(mz):
            # Try positive mode: M = m/z - proton
            target_mass = mz - proton_mass
            mode_used = 'positive'
        else:
            results.append({
                'idx': idx,
                'compound': row['Compound'],
                'formula': None,
                'mode': None,
                'ppm_error': None,
                'note': 'no mass data'
            })
            continue

        # Skip very large masses (>1000 Da) for speed
        if target_mass > 1000:
            results.append({
                'idx': idx,
                'compound': row['Compound'],
                'formula': None,
                'mode': mode_used,
                'ppm_error': None,
                'note': 'mass too large'
            })
            continue

        matches = assign_formula(target_mass, ppm_tolerance=3)

        if matches:
            best = matches[0]
            results.append({
                'idx': idx,
                'compound': row['Compound'],
                'formula': best['formula'],
                'mode': mode_used,
                'ppm_error': best['ppm_error'],
                'note': f'{len(matches)} matches'
            })
        else:
            # If positive mode failed and we were using m/z, try negative
            if mode_used == 'positive' and pd.notna(mz):
                target_mass = mz + proton_mass
                matches = assign_formula(target_mass, ppm_tolerance=3)
                if matches:
                    best = matches[0]
                    results.append({
                        'idx': idx,
                        'compound': row['Compound'],
                        'formula': best['formula'],
                        'mode': 'negative',
                        'ppm_error': best['ppm_error'],
                        'note': f'{len(matches)} matches'
                    })
                    continue

            results.append({
                'idx': idx,
                'compound': row['Compound'],
                'formula': None,
                'mode': mode_used,
                'ppm_error': None,
                'note': 'no match'
            })

    # Save results
    results_df = pd.DataFrame(results)

    # Merge with original
    output_df = df.copy()
    output_df['Assigned_Formula'] = results_df['formula'].values
    output_df['Assignment_Mode'] = results_df['mode'].values
    output_df['Assignment_PPM'] = results_df['ppm_error'].values
    output_df['Assignment_Note'] = results_df['note'].values

    output_df.to_excel('Emily_Data_WITH_FORMULAS.xlsx', index=False)

    # Summary
    assigned = results_df['formula'].notna().sum()
    print(f"\n=== RESULTS ===")
    print(f"Total compounds: {len(results_df)}")
    print(f"Formulas assigned: {assigned} ({100*assigned/len(results_df):.1f}%)")
    print(f"Output saved to: Emily_Data_WITH_FORMULAS.xlsx")

    # Show some examples
    print(f"\nExample assignments:")
    for r in results[:10]:
        if r['formula']:
            print(f"  {r['compound']}: {r['formula']} (ppm={r['ppm_error']:.2f})")

if __name__ == '__main__':
    main()
