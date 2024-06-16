library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
USE ieee.math_real.log2;
USE ieee.math_real.ceil;
USE ieee.math_real.uniform;

library work;
use work.dot_product_pkg.all;
use work.prim_ops_pkg.all;
use work.mask_util_pkg.all;

entity dot_product_tb is
end dot_product_tb;

architecture rtl of dot_product_tb is
	constant clk_freq_c   : positive := 100000000;
	constant clk_period_c : time := ((1000000000/clk_freq_c)) * 1 ns;
	constant L_c          : positive := 32; 
	constant in_dim_c     : positive := 6;
	constant D_c          : positive := 2;
	constant pipelined_c  : boolean  := true;
	constant fp_fractional_bits_c : positive := 6;

	constant pipeline_latency_c : integer := integer(ceil(log2(real((2*in_dim_c))))) + 1 + 3; -- plus 3 to account for multiplier latency

	constant generate_toggle_traces_c : boolean := false;

	constant truncation_c : boolean := false;

	signal clk_s     : std_ulogic := '0';
	signal rst_s     : std_ulogic;
	signal en_s      : std_ulogic;
	
	signal rnd_s       : std_ulogic_vector (L_c - 1 downto 0);
	signal rnd_trunc_s : std_ulogic_vector (L_c - 1 downto 0);

	signal a_s       : std_ulogic_vector (L_c * D_c * in_dim_c - 1 downto 0);
	signal b_s       : std_ulogic_vector (L_c * D_c * in_dim_c - 1 downto 0);
	signal c_s       : std_ulogic_vector (L_c * D_c - 1 downto 0);

	signal trunc_shares_s : std_ulogic_vector (L_c * D_c - 1 downto 0);

	signal result : std_ulogic_vector (L_c - 1 downto 0);

	signal result_real : real;

	type real_array is array(0 to in_dim_c - 1) of real;

	component dot_product is
		port (
			rnd_i      : in  std_logic_vector(L_c * (D_c - 1) - 1 downto 0);
			clk_i      : in  std_ulogic;
			rst_i      : in  std_ulogic;
			en_i       : in  std_ulogic;
			a_i        : in  std_logic_vector (L_c * D_c * in_dim_c - 1 downto 0);
			b_i        : in  std_logic_vector (L_c * D_c * in_dim_c - 1 downto 0);
			c_o        : out std_logic_vector (L_c * D_c - 1 downto 0)
		);
	end component;


begin

	
	dut : dot_product
	-- generic map (
	-- 	L_g          => L_c,
	-- 	D_g          => D_c,
	-- 	in_dim_g     => in_dim_c,
	-- 	pipelined_g  => pipelined_c
	-- ) 
	port map (
		rnd_i => rnd_s,
		clk_i => clk_s,
		rst_i => rst_s,
		en_i  => en_s,
		a_i   => a_s,
		b_i   => b_s,
		c_o   => c_s
	);

	
	clk_s <= not clk_s after ((1000000000/clk_freq_c)/2) * 1 ns;
	
	truncation_mode : if truncation_c = true generate

		trunc : entity work.masked_trunc
		generic map (
			L_g                   => L_c,
			D_g                   => D_c,
			fp_fractional_bits_g  => fp_fractional_bits_c
		) port map (
			shares_i        => c_s,
			rnd_i           => rnd_trunc_s,
			trunc_shares_o  => trunc_shares_s
		);

		result <= PADD(trunc_shares_s(L_c - 1 downto 0), trunc_shares_s(2*L_c - 1 downto L_c));
		result_real <= convert_fp_to_real(result);

		pipelined_test : if pipelined_c = true generate
			process 
				
				variable seed1, seed2 : integer := 999;

				impure function rand_slv(len : integer) return std_logic_vector is
					variable r : real;
					variable slv : std_logic_vector(len - 1 downto 0);
				begin
					for i in slv'range loop
						uniform(seed1, seed2, r);
						slv(i) := '1' when r > 0.5 else '0';
					end loop;
					return slv;
				end function;

				variable inputs  : real_array := (1.5, 1.5, 1.5, 1.5, 1.5, 1.5);
				variable weights : real_array := (2.0, 2.0, 2.0, 2.0, 2.0, 2.0);

				variable a_v : std_ulogic_vector (L_c * D_c * in_dim_c - 1 downto 0);
				variable b_v : std_ulogic_vector (L_c * D_c * in_dim_c - 1 downto 0);

			begin
				
				for i in 0 to in_dim_c - 1 loop
					a_v(L_c * D_c * (i + 1) - 1 downto L_c * D_c * i) := 
						mask_val(
							convert_real_to_fp(inputs(i)),
							rand_slv(L_c)					
						);
					b_v(L_c * D_c * (i + 1) - 1 downto L_c * D_c * i) := 
						mask_val(
							convert_real_to_fp(weights(i)),
							rand_slv(L_c)
						);
				end loop;

				rst_s <= '0';

				wait until falling_edge(clk_s);
				report "Reset";
				rst_s <= '1';
				wait until falling_edge(clk_s);
				rst_s <= '0';

				en_s <= '1';

				rnd_s <= rand_slv(L_c);
				rnd_trunc_s <= rand_slv(L_c);

				a_s <= a_v;
				b_s <= b_v;

				for i in 0 to pipeline_latency_c loop
					wait until falling_edge(clk_s);
				end loop;

				wait for 1 ns;
								
				report "SIMULATION FINSIHED" severity failure;
				wait;



			end process;
		end generate;

	end generate;

	no_truncation_mode : if truncation_c = false generate

		generate_toggle_traces_mode_on : if generate_toggle_traces_c = true generate
			process 
			begin
				rst_s <= '1';
				en_s <= '0';
				wait for 100 ns;
				rst_s <= '0';
				wait;
			end process;
		end generate;
		
		generate_toggle_traces_mode_off : if generate_toggle_traces_c = false generate
			pipelined_test : if pipelined_c = true generate
				process 
				begin
					
					rst_s <= '0';

					wait until falling_edge(clk_s);
					report "Reset";
					rst_s <= '1';
					wait until falling_edge(clk_s);
					rst_s <= '0';

					en_s <= '1';

					rnd_s <= X"34EAD429";
					

					-- a_s(in_dim_c - 1, share_index - 1), ..., a_s(1,1), a_s(1,0), a_s(0,1), a_s(0,0)

					a_s <=  X"F0C80AA7" & X"0F37F559" & 
							X"ADA5B58A" & X"525A4A75" & 
							X"665ED2A9" & X"99A12D57" & 
							X"AAAB0730" & X"5554F8CF" & 
							X"FD4BACBA" & X"02B45347" & 
							X"A54D1EA7" & X"5AB2E157";

					b_s <=  X"75AC2C11" & X"8A53D3EF" &
							X"0BD9D3E6" & X"F4262C1A" &
							X"7751A7E5" & X"88AE581B" &
							X"D052A750" & X"2FAD58B0" &
							X"3B49F353" & X"C4B60CAD" &
							X"2CC27605" & X"D33D89FB";

					wait until falling_edge(clk_s);

					rnd_s <= X"80000000";

					-- a_s(in_dim_c - 1, share_index - 1), ..., a_s(1,1), a_s(1,0), a_s(0,1), a_s(0,0)

					a_s <=  X"80000000" & X"80000000" & 
							X"7FFFFFFF" & X"80000000" & 
							X"80000000" & X"80000000" & 
							X"7FFFFFFF" & X"80000000" & 
							X"80000001" & X"80000000" & 
							X"7FFFFFFE" & X"80000000";

					b_s <=  X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000";

					for i in 0 to pipeline_latency_c - 1 loop
						wait until falling_edge(clk_s);
					end loop;

					wait for 1 ns;
					-- c_s(0) + c_s(1) = X"00000000"
					assert c_s(L_c - 1 downto 0) = X"B91B3A5D" severity error;
					assert c_s(L_c * 2 - 1 downto L_c) = X"46E4C5A3" severity error;

					wait until falling_edge(clk_s);
					wait for 1 ns;
					-- c_s(0) + c_s(1) = X"00000000"
					assert c_s(L_c - 1 downto 0) = X"80000000" severity error;
					assert c_s(L_c * 2 - 1 downto L_c) = X"80000000" severity error;
					report "SIMULATION FINSIHED" severity failure;
					wait;
					
				end process;

				-- for blinding architecture
				-- process 
				-- begin
					
				-- 	rst_s <= '0';

				-- 	wait until falling_edge(clk_s);
				-- 	report "Reset";
				-- 	rst_s <= '1';
				-- 	wait until falling_edge(clk_s);
				-- 	rst_s <= '0';

				-- 	en_s <= '1';

				-- 	rnd_s <= X"34EAD429";

				-- 	a_s(0)(0) <= X"5AB2E157";
				-- 	a_s(0)(1) <= X"A54D1EA7";
				-- 	b_s(0)(0) <= X"D33D89FB";
				-- 	b_s(0)(1) <= X"2CC27605";

				-- 	a_s(1)(0) <= X"02B45347";
				-- 	a_s(1)(1) <= X"FD4BACBA";
				-- 	b_s(1)(0) <= X"C4B60CAD";
				-- 	b_s(1)(1) <= X"3B49F353";

				-- 	a_s(2)(0) <= X"5554F8CF";
				-- 	a_s(2)(1) <= X"AAAB0730";
				-- 	b_s(2)(0) <= X"2FAD58B0";
				-- 	b_s(2)(1) <= X"D052A750";

				-- 	a_s(3)(0) <= X"99A12D57";
				-- 	a_s(3)(1) <= X"665ED2A9";
				-- 	b_s(3)(0) <= X"88AE581B";
				-- 	b_s(3)(1) <= X"7751A7E5";

				-- 	a_s(4)(0) <= X"525A4A75";
				-- 	a_s(4)(1) <= X"ADA5B58A";
				-- 	b_s(4)(0) <= X"F4262C1A";
				-- 	b_s(4)(1) <= X"0BD9D3E6";

				-- 	a_s(5)(0) <= X"0F37F559";
				-- 	a_s(5)(1) <= X"F0C80AA7";
				-- 	b_s(5)(0) <= X"8A53D3EF";
				-- 	b_s(5)(1) <= X"75AC2C11";

				-- 	wait until falling_edge(clk_s);

				-- 	rnd_s <= X"80000000";

				-- 	a_s(0)(0) <= X"80000000";
				-- 	a_s(0)(1) <= X"7FFFFFFE";
				-- 	b_s(0)(0) <= X"80000000";
				-- 	b_s(0)(1) <= X"80000000";

				-- 	a_s(1)(0) <= X"80000000";
				-- 	a_s(1)(1) <= X"80000001";
				-- 	b_s(1)(0) <= X"80000000";
				-- 	b_s(1)(1) <= X"80000000";

				-- 	a_s(2)(0) <= X"80000000";
				-- 	a_s(2)(1) <= X"7FFFFFFF";
				-- 	b_s(2)(0) <= X"80000000";
				-- 	b_s(2)(1) <= X"80000000";

				-- 	a_s(3)(0) <= X"80000000";
				-- 	a_s(3)(1) <= X"80000000";
				-- 	b_s(3)(0) <= X"80000000";
				-- 	b_s(3)(1) <= X"80000000";

				-- 	a_s(4)(0) <= X"80000000";
				-- 	a_s(4)(1) <= X"7FFFFFFF";
				-- 	b_s(4)(0) <= X"80000000";
				-- 	b_s(4)(1) <= X"80000000";

				-- 	a_s(5)(0) <= X"80000000";
				-- 	a_s(5)(1) <= X"80000000";
				-- 	b_s(5)(0) <= X"80000000";
				-- 	b_s(5)(1) <= X"80000000";

				-- 	for i in 0 to integer(ceil(log2(real((2*in_dim_c + 1))))) - 1 loop
				-- 		wait until falling_edge(clk_s);
				-- 	end loop;

				-- 	wait for 1 ns;
				-- 	-- c_s(0) + c_s(1) = X"00000000"
				-- 	assert c_s(0) = X"73041C9A" severity error;
				-- 	assert c_s(1) = X"8CFBE366" severity error;

				-- 	wait until falling_edge(clk_s);
				-- 	wait for 1 ns;
				-- 	-- c_s(0) + c_s(1) = X"00000000"
				-- 	assert c_s(0) = X"00000000" severity error;
				-- 	assert c_s(1) = X"00000000" severity error;
					
				-- 	report "SIMULATION FINSIHED" severity failure;
				-- 	wait;
					
				-- end process;
			end generate;

			not_pipelined_test : if pipelined_c = false generate
				process 
				begin
					
					rnd_s <= X"80000000";

					a_s <=  X"80000000" & X"80000000" & 
							X"7FFFFFFF" & X"80000000" & 
							X"80000000" & X"80000000" & 
							X"7FFFFFFF" & X"80000000" & 
							X"80000001" & X"80000000" & 
							X"7FFFFFFE" & X"80000000";

					b_s <=  X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000" &
							X"80000000" & X"80000000";

					wait until falling_edge(clk_s);
					wait for 1 ns;
					assert c_s(L_c - 1 downto 0) = X"80000000" severity error;
					assert c_s(L_c * 2 - 1 downto L_c) = X"80000000" severity error;

					rnd_s <= X"34EAD429";

					a_s <=  X"F0C80AA7" & X"0F37F559" & 
							X"ADA5B58A" & X"525A4A75" & 
							X"665ED2A9" & X"99A12D57" & 
							X"AAAB0730" & X"5554F8CF" & 
							X"FD4BACBA" & X"02B45347" & 
							X"A54D1EA7" & X"5AB2E157";

					b_s <=  X"75AC2C11" & X"8A53D3EF" &
							X"0BD9D3E6" & X"F4262C1A" &
							X"7751A7E5" & X"88AE581B" &
							X"D052A750" & X"2FAD58B0" &
							X"3B49F353" & X"C4B60CAD" &
							X"2CC27605" & X"D33D89FB";

					wait until falling_edge(clk_s);
					wait for 1 ns;
					assert c_s(L_c - 1 downto 0) = X"B91B3A5D" severity error;
					assert c_s(L_c * 2 - 1 downto L_c) = X"46E4C5A3" severity error;
					
					report "SIMULATION FINSIHED" severity failure;
					wait;
					
				end process;
			end generate;
		end generate;
	end generate;
end rtl;