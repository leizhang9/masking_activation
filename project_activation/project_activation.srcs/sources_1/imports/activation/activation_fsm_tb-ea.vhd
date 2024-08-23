library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
USE ieee.math_real.log2;
USE ieee.math_real.ceil;
USE ieee.math_real.uniform;

library work;
use work.prim_ops_pkg.all;
use work.mask_util_pkg.all;

entity activation_fsm_tb is
end activation_fsm_tb;

architecture rtl of activation_fsm_tb is
	constant clk_freq_c   : positive := 100000000;
	constant clk_period_c : time := ((1000000000/clk_freq_c)) * 1 ns;
	constant L_c          : positive := 32;
	constant D_c          : positive := 2;
	constant dim_c        : positive := 11;
	constant fp_fractional_bits_c : positive := 6;

	signal clk_s     : std_ulogic := '0';
	signal rst_s     : std_ulogic;

	signal start_s   : std_ulogic;
	signal valid_s   : std_ulogic;
	signal next_input_s : std_ulogic;
	signal next_rnd_s : std_ulogic;
	signal done_s : std_ulogic;


	signal rnd_s  : std_ulogic_vector (L_c * 19 - 1 downto 0);

	signal in_s       : std_ulogic_vector (L_c * D_c - 1 downto 0);
	signal out_s      : std_ulogic_vector (L_c * D_c - 1 downto 0);
--	signal trn_out_s  : std_ulogic_vector (L_c * D_c - 1 downto 0);


	signal result0 : std_ulogic_vector (L_c - 1 downto 0);
	signal result_real0 : real;

--	signal result1 : std_ulogic_vector (L_c - 1 downto 0);
--	signal result_real1 : real;

	type in_real_array is array(0 to dim_c - 1) of real;

	component activation_fsm is
		generic (
			L_g                  : positive := 32; -- fixed point width
			D_g                  : positive := 2 -- number of shares
		);
		port (
			clk_i        : in  std_ulogic;
			rst_i        : in  std_ulogic;
			dim_i        : in  std_ulogic_vector (L_g - 1 downto 0);
			in_i         : in  std_ulogic_vector (L_g * D_g - 1 downto 0);
			rnd_i        : in  std_ulogic_vector (19 * L_g * (D_g - 1) - 1 downto 0);
			start_i      : in  std_ulogic;
			next_input_o : out std_ulogic;
			next_rnd_o : out std_ulogic;
			valid_o      : out std_ulogic;
			done_o       : out std_ulogic;
			out_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0)
--			trn_o        : out std_ulogic_vector (L_g * D_g - 1 downto 0)
		);
	end component;


begin


	dut : activation_fsm
	generic map (
		L_g                   => L_c,
		D_g                   => D_c
	)
	port map (
		clk_i     => clk_s,
		rst_i     => rst_s,
		dim_i     => std_logic_vector(to_unsigned(dim_c, L_c)),
		in_i      => in_s,
		rnd_i     => rnd_s,
		start_i   => start_s,
		next_input_o => next_input_s,
		next_rnd_o => next_rnd_s,
		valid_o   => valid_s,
		done_o    => done_s,
		out_o     => out_s
--		trn_o     => trn_out_s
	);


	clk_s <= not clk_s after ((1000000000/clk_freq_c)/2) * 1 ns;


	result0 <= PADD(out_s(L_c - 1 downto 0), out_s(2*L_c - 1 downto L_c));
	result_real0 <= convert_fp_to_real(result0);

--	result1 <= PADD(trn_out_s(L_c - 1 downto 0), trn_out_s(2*L_c - 1 downto L_c));
--	result_real1 <= convert_fp_to_real(result1);


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

		-- variable inputs  : in_real_array   := (20.0, -1.5, 1.5, 1.5, -1.5, -1.5, 2.0, -3.0, 345.0, -478.0);
		variable inputs  : in_real_array   := (20.0, -1.5, 1.5, 1.5, -1.5, -1.5, 2.0, -3.0, 345.0, -478.0, 5.0);
		-- variable inputs  : in_real_array   := (20.0, -1.5, 1.5);
		-- variable inputs  : in_real_array   := (20.0, -1.5);

		variable in_v   : std_ulogic_vector (L_c * D_c * dim_c - 1 downto 0);

	begin

		for i in 0 to dim_c - 1 loop
			in_v(L_c * D_c * (i + 1) - 1 downto L_c * D_c * i) :=
				mask_val(
					convert_real_to_fp(inputs(i) * 2**fp_fractional_bits_c), -- convert to fixed-point and shift by fractional part because activation module applies truncation
					rand_slv(L_c)
				);
		end loop;

		rst_s <= '0';

		wait until falling_edge(clk_s);
		report "Reset";
		rst_s <= '1';
		wait until falling_edge(clk_s);
		rst_s <= '0';

		-- rnd_s <= rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c);
		-- rnd_s <= rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c);

		wait until falling_edge(clk_s);
		wait until rising_edge(clk_s);

		start_s <= '1';

		for i in 0 to dim_c - 1 loop
			rnd_s <= rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c) & rand_slv(L_c);
			in_s    <= "00000000000000000000000"&in_v(L_c * D_c * (i+1)-55-1 downto L_c * D_c * (i)) & "00000000000000000000000"&in_v(L_c * D_c * (i+1)-45-1 downto L_c * D_c * (i+1)-54);
			start_s <= '1';
			wait until rising_edge(clk_s);
			start_s <= '0';
			wait until valid_s = '1';
		end loop;




		-- for i in 0 to pipeline_latency_c loop
		-- 	wait until falling_edge(clk_s);
		-- end loop;

		-- wait for 1 ns;

		--report "SIMULATION FINSIHED" severity failure;
		wait;


	end process;

end rtl;
