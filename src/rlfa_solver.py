import os
import time
import random
import argparse

from collections import deque

#  CORE CSP LIBRARY (Adapted from AIMA csp.py)
def count(seq):
    return sum(bool(x) for x in seq)

def first(iterable, default=None):
    try:
        return next(iter(iterable))
    except StopIteration:
        return default

def argmin_random_tie(seq, key):
    return min(seq, key=lambda x: (key(x), random.random()))

class CSP:
    def __init__(self, variables, domains, neighbors, constraints):
        variables = variables or list(domains.keys())
        self.variables = variables
        self.domains = domains
        self.neighbors = neighbors
        self.constraints = constraints
        self.curr_domains = None
        self.nassigns = 0

    def assign(self, var, val, assignment):
        assignment[var] = val
        self.nassigns += 1

    def unassign(self, var, assignment):
        if var in assignment:
            del assignment[var]

    def nconflicts(self, var, val, assignment):
        conflicts = 0
        for v in self.neighbors[var]:
            if v in assignment:
                if not self.constraints(var, val, v, assignment[v]):
                    conflicts += 1
        return conflicts

    def display(self, assignment):
        print(assignment)

    def support_pruning(self):
        if self.curr_domains is None:
            self.curr_domains = {v: list(self.domains[v]) for v in self.variables}

    def suppose(self, var, value):
        self.support_pruning()
        removals = [(var, a) for a in self.curr_domains[var] if a != value]
        self.curr_domains[var] = [value]
        return removals

    def prune(self, var, value, removals):
        self.curr_domains[var].remove(value)
        if removals is not None:
            removals.append((var, value))

    def choices(self, var):
        return (self.curr_domains or self.domains)[var]

    def restore(self, removals):
        for B, b in removals:
            self.curr_domains[B].append(b)

# Search Algorithms

def backtracking_search(csp, select_unassigned_variable, order_domain_values, inference):
    def recursive_backtracking(assignment):
        if len(assignment) == len(csp.variables):
            return assignment
        
        var = select_unassigned_variable(assignment, csp)
        
        for value in order_domain_values(var, assignment, csp):
            if 0 == csp.nconflicts(var, value, assignment):
                csp.assign(var, value, assignment)
                
                removals = csp.suppose(var, value)
                
                if inference(csp, var, value, assignment, removals):
                    result = recursive_backtracking(assignment)
                    if result is not None:
                        return result
                
                csp.restore(removals)
        
        csp.unassign(var, assignment)
        return None

    return recursive_backtracking({})

def unordered_domain_values(var, assignment, csp):
    return csp.choices(var)

def min_conflicts(csp, max_steps=100000):
    csp.curr_domains = None
    assignment = {}

    for var in csp.variables:
        val = min_conflicts_value(csp, var, assignment)
        csp.assign(var, val, assignment)
        
    for i in range(max_steps):
        conflicted = [v for v in csp.variables if csp.nconflicts(v, assignment[v], assignment) > 0]
        if not conflicted:
            return assignment
        var = random.choice(conflicted)
        val = min_conflicts_value(csp, var, assignment)
        csp.assign(var, val, assignment)
        
    return None

def min_conflicts_value(csp, var, current_assignment):
    return argmin_random_tie(csp.domains[var], key=lambda val: csp.nconflicts(var, val, current_assignment))

# RLFA PARSE

class RLFAParser:
    def __init__(self, folder_path, instance_id):
        self.folder_path = folder_path
        self.instance_id = instance_id

    def read_domains(self):
        filename = os.path.join(self.folder_path, f"dom{self.instance_id}.txt")
        domains_lookup = {}
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:
                    parts = list(map(int, line.split()))
                    if not parts: continue
                    dom_id = parts[0]
                    values = parts[2:]
                    domains_lookup[dom_id] = values
            return domains_lookup
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
            return {}

    def read_variables(self, domains_lookup):
        filename = os.path.join(self.folder_path, f"var{self.instance_id}.txt")
        variables = []
        var_domains = {}
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:
                    parts = list(map(int, line.split()))
                    if not parts: continue
                    var_id = parts[0]
                    dom_id = parts[1]
                    variables.append(var_id)
                    var_domains[var_id] = domains_lookup.get(dom_id, [])
            return variables, var_domains
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
            return [], {}

    def read_constraints(self):
        filename = os.path.join(self.folder_path, f"ctr{self.instance_id}.txt")
        constraints_list = []
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                for line in lines[1:]:
                    parts = line.split()
                    if not parts: continue
                    
                    try:
                        var1 = int(parts[0])
                        var2 = int(parts[1])
                        operator = parts[2] 
                        k_value = int(parts[3])
                        
                        constraints_list.append({
                            'scope': (var1, var2),
                            'op': operator,
                            'k': k_value
                        })
                    except (IndexError, ValueError):
                        continue
                        
            return constraints_list
        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
            return []

# RLFA CSP CLASS

class RLFACSP(CSP):
    def __init__(self, variables, domains, constraints_data):
        self.constraints_data = constraints_data
        neighbors = {v: [] for v in variables}
        self.constraint_map = {} 

        for c in constraints_data:
            u, v = c['scope']
            if u in neighbors and v in neighbors:
                if v not in neighbors[u]: neighbors[u].append(v)
                if u not in neighbors[v]: neighbors[v].append(u)
                
                key = (u, v) if u < v else (v, u)
                if key not in self.constraint_map:
                    self.constraint_map[key] = []
                self.constraint_map[key].append(c)

        super().__init__(variables, domains, neighbors, self.rlfa_constraint_check)
        self.constraint_weights = {key: 1 for key in self.constraint_map.keys()}

    def rlfa_constraint_check(self, A, a, B, b):
        key = (A, B) if A < B else (B, A)
        
        if key not in self.constraint_map:
            return True 
            
        diff = abs(a - b)
        for rule in self.constraint_map[key]:
            if rule['op'] == '>' and diff <= rule['k']:
                return False
            elif rule['op'] == '=' and diff != rule['k']:
                return False
        return True

# HEURISTICS & INFERENCE (dom/wdeg)

def dom_wdeg_heuristic(assignment, csp):
    unassigned = [v for v in csp.variables if v not in assignment]
    if not unassigned: return None

    best_ratio = float('inf')
    best_var = unassigned[0]

    for var in unassigned:
        d_size = len(csp.curr_domains[var]) if csp.curr_domains else len(csp.domains[var])
        
        wdeg = 0
        for neighbor in csp.neighbors[var]:
            if neighbor not in assignment:
                key = (var, neighbor) if var < neighbor else (neighbor, var)
                if key in csp.constraint_weights:
                    wdeg += csp.constraint_weights[key]
        
        if wdeg == 0: wdeg = 1
        ratio = d_size / wdeg
        
        if ratio < best_ratio:
            best_ratio = ratio
            best_var = var
            
    return best_var

def fc_wdeg(csp, var, value, assignment, removals):
    csp.support_pruning()
    for B in csp.neighbors[var]:
        if B not in assignment:
            for b in csp.curr_domains[B][:]:
                if not csp.constraints(var, value, B, b):
                    csp.prune(B, b, removals)
            if not csp.curr_domains[B]:
                key = (var, B) if var < B else (B, var)
                if key in csp.constraint_weights:
                    csp.constraint_weights[key] += 1
                return False
    return True

def mac_wdeg(csp, var, value, assignment, removals):
    queue = deque([(X, var) for X in csp.neighbors[var]])
    return ac3_wdeg(csp, queue, removals)

def ac3_wdeg(csp, queue=None, removals=None):
    if queue is None:
        queue = [(Xi, Xk) for Xi in csp.variables for Xk in csp.neighbors[Xi]]
    
    csp.support_pruning()
    
    while queue:
        Xi, Xj = queue.popleft()
        if revise(csp, Xi, Xj, removals):
            if not csp.curr_domains[Xi]:
                key = (Xi, Xj) if Xi < Xj else (Xj, Xi)
                if key in csp.constraint_weights:
                    csp.constraint_weights[key] += 1
                return False
            
            for Xk in csp.neighbors[Xi]:
                if Xk != Xj:
                    queue.append((Xk, Xi))
    return True

def revise(csp, Xi, Xj, removals):
    revised = False
    for x in csp.curr_domains[Xi][:]:
        is_consistent = False
        for y in csp.curr_domains[Xj]:
            if csp.constraints(Xi, x, Xj, y):
                is_consistent = True
                break
        if not is_consistent:
            csp.prune(Xi, x, removals)
            revised = True
    return revised

# MAIN

def solve_rlfa(csp, algorithm="FC"):
    start_time = time.process_time()
    
    if algorithm == "FC":
        inference = fc_wdeg
    elif algorithm == "MAC":
        inference = mac_wdeg
    elif algorithm == "MINCONFLICTS":
        result = min_conflicts(csp, max_steps=10000)
        duration = time.time() - start_time
        return result, duration, csp.nassigns
    
    if algorithm in ["FC", "MAC"]:
        result = backtracking_search(
            csp,
            select_unassigned_variable=dom_wdeg_heuristic,
            order_domain_values=unordered_domain_values,
            inference=inference
        )
    
    duration = time.process_time() - start_time
    return result, duration, csp.nassigns

if __name__ == '__main__':
    cli_parser = argparse.ArgumentParser(description="RLFA Optimization Engine")
    cli_parser.add_argument("-i", "--instance", type=str, default="11", help="Instance ID to solve (e.g., 11, 8-f10)")
    args = cli.parser.parse_args()

    folder_path = '../data/rlfap' 
    instance_id = args.instance 
    
    print(f"--- Loading Instance {instance_id} ---")
    parser = RLFAParser(folder_path, instance_id)
    
    doms = parser.read_domains()
    if not doms:
        print(f"Error: Domains not found for instance {instance_id} Exiting.")
        exit(1)
        
    vars_list, var_domains = parser.read_variables(doms)
    ctrs = parser.read_constraints()
    
    print(f"Variables: {len(vars_list)}")
    print(f"Constraints: {len(ctrs)}")
    
    # 1. FC
    print("\n--- Running FC with dom/wdeg ---")
    csp_fc = RLFACSP(vars_list, var_domains, ctrs)
    res_fc, time_fc, assigns_fc = solve_rlfa(csp_fc, "FC")
    print(f"Result: {'Solved' if res_fc else 'Failed'}, Time: {time_fc:.4f}s, Assignments: {assigns_fc}")
    
    # 2. MAC
    print("\n--- Running MAC with dom/wdeg ---")
    csp_mac = RLFACSP(vars_list, var_domains, ctrs)
    res_mac, time_mac, assigns_mac = solve_rlfa(csp_mac, "MAC")
    print(f"Result: {'Solved' if res_mac else 'Failed'}, Time: {time_mac:.4f}s, Assignments: {assigns_mac}")
    
    # # 3. MinConflicts
    # print("\n--- Running MinConflicts ---")
    # csp_mc = RLFACSP(vars_list, var_domains, ctrs)
    # res_mc, time_mc, _ = solve_rlfa(csp_mc, "MINCONFLICTS")
    # print(f"Result: {'Solved' if res_mc else 'Failed'}, Time: {time_mc:.4f}s")
